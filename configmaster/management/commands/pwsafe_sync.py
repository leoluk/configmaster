from django.conf import settings
from django.core.management import BaseCommand
import json
import requests
from configmaster.models import Device, DeviceGroup, DeviceType


class Command(BaseCommand):
    help = "Import data from PasswordSafe"

    # noinspection PyMethodMayBeStatic
    def add_arguments(self, parser):
        parser.add_argument('filename', default="", help="Read from file instead of remote server")

    def fetch_pwsafe_data(self, url=settings.PWSAFE_EXPORT_URL):
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
        else:
            self.stderr.write("Failed to connect to PasswordSafe")

    @staticmethod
    def fetch_pwsafe_data_from_file(filename):
        return json.load(open(filename))

    def handle(self, *args, **options):
        if not len(args):
            pwsafe_export = self.fetch_pwsafe_data()
        else:
            pwsafe_export = self.fetch_pwsafe_data_from_file(args[0])

        for label, data in pwsafe_export.iteritems():
            self.stdout.write("Processing %s..." % label)
            device = Device.objects.get_or_create(label=label)[0]
            group = DeviceGroup.objects.get_or_create(name=data['device_group'])[0]
            device.group = group
            device.name = data['name']
            device.hostname = data['hostname']
            device.sync = True

            if "tmp_remote_enabled" in data:
                device.enabled = data['tmp_remote_enabled']
                if not len(data['tmp_device_type']):
                    device.device_type = None
                else:
                    device_type = DeviceType.objects.get_or_create(name=data['tmp_device_type'])[0]
                    device.device_type = device_type

            device.save()
