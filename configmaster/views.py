from django.views.generic import TemplateView


class DashboardView(TemplateView):
    template_name = 'configmaster/dashboard.html'
