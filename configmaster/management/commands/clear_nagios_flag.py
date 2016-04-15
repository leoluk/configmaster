#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in Device.objects.all():
            if device.known_by_nagios:
                device.known_by_nagios = False
                device.save()