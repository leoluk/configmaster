from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in Device.objects.order_by('group__name'):
            if device.latest_reports.count() and not device.known_by_nagios:
                self.stdout.write("%s %s (%s) has reports, but is not known to Nagios" %(device.group, device.label, device.hostname))