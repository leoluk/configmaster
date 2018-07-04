#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

import json
import traceback
from django.conf import settings
from django.core.exceptions import SuspiciousOperation

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseBadRequest, \
    HttpResponse
from django.shortcuts import render_to_response, redirect
from django.utils.timezone import localtime

from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, View

from configmaster.management.handlers.base import TaskExecutionError
from configmaster.management.handlers.password_change import \
    PasswordChangeHandler

from configmaster.models import Device, Task, DeviceGroup


class DashboardView(ListView):
    template_name = 'configmaster/dashboard.html'
    queryset = (Device.objects.order_by('-enabled', 'group', 'name')
                .prefetch_related("latest_reports")
                .prefetch_related("latest_reports__task")
                .exclude(latest_reports__isnull=True))

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        # TODO: add a "show inactive devices" button
        context['hidden_devices'] = Device.objects.filter(
            latest_reports__isnull=True).count()
        return context


class VersionInfoView(ListView):
    template_name = 'configmaster/version_info.html'
    queryset = (DeviceGroup.objects.prefetch_related("device_set")
                .prefetch_related("device_set__device_type"))


class DashboardRunView(View):
    def post(self, request, *args, **kwargs):
        try:
            device = Device.objects.get(label=request.POST['device'])
            task = Task.objects.get(id=request.POST['task'])
        except (Device.DoesNotExist, Task.DoesNotExist):
            return HttpResponseBadRequest("No such device or task")

        call_command("run", device.label, "T-%d" % task.id)

        report = device.latest_reports.filter(task=task).first()

        # Task disabled - remove row
        if not report:
            return HttpResponse("")

        return render_to_response("configmaster/dashboard_row.html", {
            "device": device, "report": report,
            "additional_task": list(device.latest_reports.order_by("task__id")).index(report)
        })


class DeviceGetVersionAPIView(View):
    def get(self, request, *args, **kwargs):
        try:
            device = Device.objects.get(label=request.GET['device'])
        except Device.DoesNotExist:
            return HttpResponseBadRequest("No such device")
        except KeyError:
            return HttpResponseBadRequest("Missing parameter")

        return HttpResponse(json.dumps({
            'label': device.label,
            'hostname': device.hostname,
            'version': device.version_info}),
        content_type='application/json')


class DeviceStatusAPIView(View):
    def get(self, request, *args, **kwargs):
        try:
            device = Device.objects.get(label=request.GET['device'])
            task = Task.objects.get(id=request.GET['task'])
        except Device.DoesNotExist:
            return HttpResponseBadRequest("No such device")
        except Task.DoesNotExist:
            return HttpResponseBadRequest("No such task")
        except KeyError:
            return HttpResponseBadRequest("Missing parameter")

        device.known_by_nagios = True
        device.save()

        report = device.get_latest_report_for_task(task)
        status = device.get_status_for_report(report)

        if task.master_task and status != device.STATUS_SUCCESS:
            master_report = device.get_latest_report_for_task(task.master_task)
            if master_report:
                master_status = device.get_status_for_report(master_report)
                if master_status != device.STATUS_SUCCESS:
                    return HttpResponse("Disabled: main check failed",
                                        content_type='text/plain')

        status_text = dict(device.STATUS_CHOICES)[status]

        if status in (device.STATUS_SUCCESS, device.STATUS_ERROR):
            status_text += ": " + report.output

        if report and report.long_output:
            url = reverse('admin:%s_%s_change' %(
                report._meta.app_label, report._meta.model_name),
                          args=[report.id] )
            url = request.build_absolute_uri(url)

            if device.group.is_security_sensitive:
                status_text += (
                    '\n\n(security sensitive device, output omitted - see %s)'
                    % url)
            else:
                status_text += (
                    ('\n\nReport: %s' % url)+'\n\n'+report.long_output)

        if report:
            status_text += (
                '\n\nNOTICE: This check is executed by ConfigMaster. '
                'The last run was at %s.\nYou can manually trigger a run using'
                ' the ConfigMaster web interface or command line.' % (
                    localtime(report.date).strftime("%Y-%m-%d %H:%M:%S")
                )
            )

        return HttpResponse(status_text, content_type='text/plain')


class PasswordChangeAPIView(View):
    """
    Password change API handler.

    HTTP POST parameters:

        device: device label, assumed to be in the ConfigMaster database
        username: login username
        current_password: currently valid password for device login
        new_password: password to be set

    Right now, this view uses the same libraries, but is not coupled to the
    task runner since the password change task does not fit the current task
    model (for example: additional, secret parameters). We provide an API
    endpoint for external services to use, and the task queue and the
    external service is responsible for dealing with the result. We still
    want to use the ConfigMaster SSH connection settings for devices managed
    by ConfigMaster. This means that this view calls the device handlers
    itself (re-consider when T47 is implemented!) and needs to handle all
    possible failures that run.py handles.

    """

    def post(self, request, *args, **kwargs):
        try:
            api_key = request.POST['api_key']

            if api_key != settings.CONFIGMASTER_PW_CHANGE_API_KEY:
                return HttpResponseBadRequest(
                    "Invalid API key")

            username = request.POST['username']
            current_password = request.POST['current_password']
            new_password = request.POST['new_password']
            device = Device.objects.get(label=request.POST['device'])
        except Device.DoesNotExist:
            return HttpResponse(json.dumps({
                'result': 'unknown',
                'message': "No such device"}))

        except KeyError:
            return HttpResponseBadRequest("Missing parameter")

        try:
            handler = PasswordChangeHandler(
                device, current_password, new_password, username)
            with handler.run_wrapper():
                try:
                    state, result = handler.run()
                finally:
                    handler.cleanup()
                if result is None:
                    raise TaskExecutionError(
                        "Task handler did not return any data")
        except TaskExecutionError as e:
            return HttpResponse(json.dumps({
                'result': 'failure',
                'message': (
                    'Task failed with an error message:\n\n' +
                    str(e) + '\n\n' + (e.long_message or ""))}))
        except Exception as e:
            return HttpResponse(json.dumps({
                'result': 'failure',
                'message': (
                    'Exception during task execution:\n\n' +
                    str(e) + '\n\n' + traceback.format_exc())}))

        return HttpResponse(json.dumps({
            'result': 'success',
            'message': result}))

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if not settings.CONFIGMASTER_PW_CHANGE_API_KEY:
            raise SuspiciousOperation("Disabled PW change endpoint accessed")

        return super(PasswordChangeAPIView, self).dispatch(
            request, *args, **kwargs)


class RedirectView(View):
    def get(self, request, *args, **kwargs):
        try:
            type_ = request.GET['type']
            if type_ not in ('report', 'result'):
                return HttpResponseBadRequest("Invalid parameter")
            device = Device.objects.get(label=request.GET['device'])
            task = Task.objects.get(id=request.GET['task'])
            report = device.get_latest_report_for_task(task)

            if not report:
                return HttpResponseBadRequest("No report for task")

        except Device.DoesNotExist:
            return HttpResponseBadRequest("No such device")
        except Task.DoesNotExist:
            return HttpResponseBadRequest("No such task")
        except KeyError:
            return HttpResponseBadRequest("Missing parameter")

        if type_ == 'report':
            return redirect(reverse('admin:%s_%s_change' %(
                report._meta.app_label, report._meta.module_name),
                          args=[report.id]))
        elif type_ == 'result':
            return redirect(report.result_url)
