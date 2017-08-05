#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    """
    Clears the Nagios flag from all device objects. Whenever Nagios requests
    a specific device, the :attr:`configmaster.models.Device.known_by_nagios`
    flag is set.

    This lets you determine whether there are devices which are not monitored
    by Nagios (by filtering for them in the Django admin).

    See Also:
        :mod:`configmaster.management.commands.show_devices_not_in_nagios`

    """

    help = "Unset all known_by_nagios flags"

    def handle(self, *args, **options):
        for device in Device.objects.all():
            if device.known_by_nagios:
                device.known_by_nagios = False
                device.save()