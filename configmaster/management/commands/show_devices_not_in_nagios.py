from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in Device.objects.all():
            if device.latest_reports.count() and not device.known_by_nagios:
                self.stdout.write("Device %s (%s) has reports, but is not known to Nagios" %(device.label, device.hostname))