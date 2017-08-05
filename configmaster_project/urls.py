#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.conf.urls import include, url

from django.contrib import admin
import configmaster.urls

admin.autodiscover()

urlpatterns = (
    url(r'^admin/', include(admin.site.urls)),
    url(r'^adminactions/', include('adminactions.urls')),

    url(r'', include(configmaster.urls)),
)
