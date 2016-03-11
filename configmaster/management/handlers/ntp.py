from datetime import datetime

from django.conf import settings

from configmaster.management.handlers.base import TaskExecutionError

from configmaster.management.handlers.network_device import \
    NetworkDeviceHandler

from django.utils import timezone


class NetworkDeviceNTPHandler(NetworkDeviceHandler):
    def run(self, *args, **kwargs):
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
