#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView
from configmaster import views

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url=reverse_lazy('dashboard'))),
    url(r'^dashboard$',(views.DashboardView.as_view()), name='dashboard'),
    url(r'^dashboard/run_task$',(views.DashboardRunView.as_view()), name='dashboard_run_task'),
    url(r'^version_info',(views.VersionInfoView.as_view()), name='version_info'),
    url(r'^api/device_status$', views.DeviceStatusAPIView.as_view()),
    url(r'^api/device_version$', views.DeviceGetVersionAPIView.as_view()),
    url(r'^api/password_change', views.PasswordChangeAPIView.as_view()),
    url(r'^api/redirect_to', views.RedirectView.as_view()),
)
