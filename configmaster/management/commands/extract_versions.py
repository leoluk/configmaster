from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in Device.objects.all():
            if not device.device_type:
                continue
            if device.device_type.version_regex:
                device.version_info = device._version_info
                device.save()