#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from datetime import datetime

from django.conf import settings

from configmaster.management.handlers.base import TaskExecutionError

from configmaster.management.handlers.network_device import \
    NetworkDeviceHandler

from django.utils import timezone


class NetworkDeviceNTPHandler(NetworkDeviceHandler):
    def __init__(self, device):
        """
        This handler compares the device's time with the local and fails
        if the offset exceeds :option:`CONFIGMASTER_NTP_MAX_DELTA`.

        The remote control must implement the ``get_time()`` interface.

        It assumes that all devices are set to same timezone as the
        ConfigMaster host.
        """

        super(NetworkDeviceNTPHandler, self).__init__(device)

    def run(self, *args, **kwargs):
        # TODO: handle per-device timezones

        time = timezone.make_aware(
            self.connection.get_time(),
            timezone.get_current_timezone())

        localtime = timezone.localtime(timezone.now())
        delta = localtime - time

        if abs(delta.total_seconds()) > settings.CONFIGMASTER_NTP_MAX_DELTA:
            self._fail_long_message(
                "Time delta exceeds limit (%ds): %.02fs" % (
                    settings.CONFIGMASTER_NTP_MAX_DELTA,
                    delta.total_seconds(),
                ),
                "Local time: %s\nRemote time: %s" % (localtime, time)
            )

        return self._return_success("Time delta: %.02f s" % delta.total_seconds())
