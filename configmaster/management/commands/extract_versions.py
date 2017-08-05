#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    """
    Manually set the device version field for all devices.

    This command is only useful for debugging or after changing the
    extraction regexp. The version info is automatically set whenever a
    config backup task runs.

    """

    def handle(self, *args, **options):
        for device in Device.objects.all():
            if not device.device_type:
                continue
            if device.device_type.version_regex:
                device.version_info = device._version_info
                device.save()