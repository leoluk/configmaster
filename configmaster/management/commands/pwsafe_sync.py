from django.conf import settings
from django.core.management import BaseCommand, call_command
import json
import requests

from configmaster.models import Device, DeviceGroup, DeviceType


class Command(BaseCommand):
    """
    This management command imports basic device data (group, label,
    description, hostname) from PWSafe, which in turn imports it from
    AssetDB.
    
    
    """

    # TODO: propagate out-of-service state (T55)

    help = "Import data from PasswordSafe"

    # noinspection PyMethodMayBeStatic
    def add_arguments(self, parser):
        parser.add_argument('filename', default="", help="Read from file instead of remote server")

    def fetch_pwsafe_data(self, url=settings.PWSAFE_EXPORT_URL):
        """
        Fetches and returns a JSON document containing all exported
        devices from PWSafe, indexed by their C-label.

        Example (one device):

        {
          "C123": {
            "hostname": "pwsafe.continum.net",
            "name": "Something something Firewall",
            "device_group": "Firewall"
        }

        """

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

            try:
                group = DeviceGroup.objects.get(name=data['device_group'])
            except DeviceGroup.DoesNotExist:
                self.stderr.write("Group %s does not exist" % data['device_group'])
                continue

            try:
                device = Device.objects.get(label=label)
            except Device.DoesNotExist:
                if data['out_of_service']:
                    continue
                else:
                    device = Device(label=label)
                    if group.default_device_type:
                        device.device_type = group.default_device_type
            else:
                if data['out_of_service']:
                    self.stdout.write("Device %s out of service, deleting..." % label)
                    device.delete()
                    continue

            device.group = group
            device.name = data['name']
            device.hostname = data['hostname']
            device.sync = True

            # During the config management migration from PWSafe to Config-
            # master, the export contained a few additional fields with
            # information which was previously stored in the PWSafe database,
            # but is now managed by ConfigMaster.

            if "tmp_remote_enabled" in data:
                device.enabled = data['tmp_remote_enabled']
                if not len(data['tmp_device_type']):
                    device.device_type = None
                else:
                    device_type = DeviceType.objects.get_or_create(name=data['tmp_device_type'])[0]
                    device.device_type = device_type

            device.save()

        call_command("archive_old_configs", stdout=self.stdout, stderr=self.stderr)