from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseNotFound, HttpResponseBadRequest, \
    HttpResponse
from django.shortcuts import render_to_response
from django.views.generic import ListView, View

from configmaster.models import Device, Task, DeviceGroup


class DashboardView(ListView):
    template_name = 'configmaster/dashboard.html'
    queryset = Device.objects.order_by('-enabled', 'group', 'name').select_related('group__name').prefetch_related("latest_reports").prefetch_related("latest_reports__task")


class VersionInfoView(ListView):
    template_name = 'configmaster/version_info.html'
    queryset = DeviceGroup.objects.prefetch_related("device_set").prefetch_related("device_set__device_type")


class DashboardRunView(View):
    def post(self, request, *args, **kwargs):
        try:
            device = Device.objects.get(label=request.REQUEST['device'])
            task = Task.objects.get(id=request.REQUEST['task'])
        except (Device.DoesNotExist, Task.DoesNotExist):
            return HttpResponseNotFound("No such device or task")

        call_command("run", device.label, "T-%d" % task.id)

        report = device.latest_reports.filter(task=task).first()

        # Task disabled - remove row
        if not report:
            return HttpResponse("")

        return render_to_response("configmaster/dashboard_row.html", {
            "device": device, "report": report,
            "additional_task": list(device.latest_reports.order_by("task__id")).index(report)
        })


class DeviceStatusAPIView(View):
    def get(self, request, *args, **kwargs):
        try:
            device = Device.objects.get(label=request.REQUEST['device'])
            task = Task.objects.get(id=request.REQUEST['task'])
        except Device.DoesNotExist:
            return HttpResponseNotFound("No such device")
        except Task.DoesNotExist:
            return HttpResponseBadRequest("No such task")
        except KeyError:
            return HttpResponseBadRequest("Missing parameter")

        report = device.get_latest_report_for_task(task)
        status = device.get_status_for_report(report)

        status_text = dict(device.STATUS_CHOICES)[status]

        if status in (device.STATUS_SUCCESS, device.STATUS_ERROR):
            status_text += ": " + report.output

        if report and report.long_output:
            url = reverse('admin:%s_%s_change' %(
                report._meta.app_label, report._meta.module_name),
                          args=[report.id] )
            url = request.build_absolute_uri(url)

            if device.group.is_security_sensitive:
                status_text += '\n\n(security sensitive device, output omitted - see %s)' % url
            else:
                status_text += '\n\n'+report.long_output+", report: %s" % report

        return HttpResponse(status_text, content_type='text/plain')



