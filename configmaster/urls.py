from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView
from configmaster import views

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url=reverse_lazy('dashboard'))),
    url(r'^dashboard$',(views.DashboardView.as_view()), name='dashboard'),
    url(r'^version_info',(views.VersionInfoView.as_view()), name='version_info'),
    url(r'^api/device_status$', views.DeviceStatusAPIView.as_view()),
)
