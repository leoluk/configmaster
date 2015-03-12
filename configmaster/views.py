from django.http.response import HttpResponseNotFound, HttpResponseBadRequest, \
    HttpResponse
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, View

from configmaster.models import Device, Task, DeviceGroup


class DashboardView(ListView):
    template_name = 'configmaster/dashboard.html'
    queryset = Device.objects.order_by('-enabled', 'group', 'name').select_related('group__name').prefetch_related("latest_reports").prefetch_related("latest_reports__task")


class VersionInfoView(ListView):
    template_name = 'configmaster/version_info.html'
    queryset = DeviceGroup.objects.prefetch_related("device_set").prefetch_related("device_set__device_type")


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

        return HttpResponse(status_text, content_type='text/plain')



