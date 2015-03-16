from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in Device.objects.all():
            if device.known_by_nagios:
                device.known_by_nagios = False
                device.save()