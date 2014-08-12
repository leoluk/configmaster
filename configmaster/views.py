from django.http.response import HttpResponseNotFound, HttpResponseBadRequest, \
    HttpResponse
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, View

from configmaster.models import Device, Task

class DashboardView(ListView):
    template_name = 'configmaster/dashboard.html'
    queryset = Device.objects.order_by('-enabled', 'group', 'name').select_related('latest_report__date', 'latest_report__output', 'group__name')

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
            status_text += ": " + device.latest_report.output

        return HttpResponse(status_text, content_type='text/plain')



