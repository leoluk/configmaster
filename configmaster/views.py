from django.views.generic import ListView

from configmaster.models import Device


class DashboardView(ListView):
    template_name = 'configmaster/dashboard.html'
    queryset = Device.objects.order_by('-enabled', 'name')
