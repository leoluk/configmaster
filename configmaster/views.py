from django.views.generic import ListView

from configmaster.models import Device


class DashboardView(ListView):
    template_name = 'configmaster/dashboard.html'
    queryset = Device.objects.order_by('-enabled', 'group', 'name').filter(enabled=True).select_related('latest_report__date', 'latest_report__output', 'group__name')
