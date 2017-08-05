#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    """
    Outputs a list of devices which have reports (which indicates that their
    FQDNs resolve and the device probably exists), but aren't monitored by
    Nagios.

    See Also:
        :mod:`configmaster.management.commands.clear_nagios_flag`

    """
    def handle(self, *args, **options):
        for device in Device.objects.order_by('group__name'):
            if (device.latest_reports.count() and not device.known_by_nagios
                and device.is_enabled()):
                self.stdout.write(
                    "%s %s (%s) has reports, but is not known to Nagios"
                    %(device.group, device.label, device.hostname))