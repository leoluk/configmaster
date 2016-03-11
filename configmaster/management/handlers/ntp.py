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

        delta = timezone.localtime(timezone.now()) - time

        if abs(delta.total_seconds()) > settings.CONFIGMASTER_NTP_MAX_DELTA:
            raise TaskExecutionError(
                "Time delta exceeds limit (%ds): %.02fs, date: %s" % (
                    settings.CONFIGMASTER_NTP_MAX_DELTA,
                    delta.total_seconds(),
                    time
                )
            )

        return self._return_success("Time delta: %.02f s" % delta.total_seconds())
