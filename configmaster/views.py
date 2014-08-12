from django.http.response import HttpResponseNotFound, HttpResponseBadRequest, \
    HttpResponse
from django.views.generic import ListView, View

from configmaster.models import Device, Task


class DashboardView(ListView):
    template_name = 'configmaster/dashboard.html'
    queryset = Device.objects.order_by('-enabled', 'group', 'name').select_related('latest_report__date', 'latest_report__output', 'group__name')

class DeviceStatusAPIView(View):
    def get(self, request, *args, **kwargs):
        try:
            device = Device.objects.get(label=request.REQUEST['device'])
            # TODO: multiple tasks, T116
            task = Task.objects.get(id=request.REQUEST['task'])
        except Device.DoesNotExist:
            return HttpResponseNotFound("No such device")
        except Task.DoesNotExist:
            return HttpResponseBadRequest("No such task")
        except KeyError:
            return HttpResponseBadRequest("Missing parameter")

        status_text = dict(device.STATUS_CHOICES)[device.status]

        if device.latest_report is not None:
            status_text += ": " + device.latest_report.output

        return HttpResponse(status_text, content_type='text/plain')



