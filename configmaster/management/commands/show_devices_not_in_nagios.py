#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in Device.objects.order_by('group__name'):
            if device.latest_reports.count() and not device.known_by_nagios and device.is_enabled():
                self.stdout.write("%s %s (%s) has reports, but is not known to Nagios" %(device.group, device.label, device.hostname))