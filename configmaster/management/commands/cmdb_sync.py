#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.conf import settings
from django.core.management import BaseCommand, call_command
import json
import requests

from configmaster.models import Device, DeviceGroup, DeviceType


class Command(BaseCommand):
    """
    Imports basic device data (group, label, description and hostname) from
    an external CMDB using a generic, JSON-based interface that the CMDB is
    expected to implement.

    If you want to connect ConfigMaster with your CMDB of choice, you have
    these options:

    * You configure or extend your CMDB to export data in the correct format
      (if your CMDB is sufficiently extensible, this is the best option)

    * You subclass this management command and override fetch_cmdb_data.

    * If that somehow doesn't work, you'll need to develop an intermediary
      server that talks to your CMDB and exposes an endpoint that exports the
      data in the format ConfigMaster expects. This is probably the least
      attractive choice.

    If you modify ConfigMaster, your best bet is to contribute those changes
    back to the upstream project on GitHub. That way, you do not have to
    maintain your own fork and we take care of maintaining your extension
    when we change our internal API (which has no stability guarantees).

    You can optionally run the command with a filename argument. If a filename
    is specified, the CMDB data is loaded from a local file instead of
    downloading it.

    """

    help = "Import data from generic CMDB"

    # noinspection PyMethodMayBeStatic
    def add_arguments(self, parser):
        parser.add_argument(
            'filename',
            nargs='?',
            default="",
            help="Read from file instead of remote server",
        )

    def fetch_cmdb_data(self, url):
        """
        Fetches and returns a dictionary containing all imported
        devices. The key is the device identifier. The value is another
        dictionary that describes the device in question.

        The following device attributes are recognized:

        *hostname*
            The fully-qualified domain name. In most environments, the FQDN
            is also used as the device identifier, in which case it will be
            equal to the key.
        *name*
            A human-readable device name. Useful if your hostname is, say,
            an alphanumeric identifier, but your CMDB has additional metadata.
        *device_group*
            The device group (not to be mistaken with the device type!) of the
            device. Device groups are categories like "Firewall",
            "Load Balancer" or "Switch" or whatever else your CMDB groups
            devices by. It is automatically created in ConfigMaster if it
            did not exist before.
        *out_of_service*
            ConfigMaster permanently deletes any device that has this flag set
            to True. The device's config will at some point be moved to the
            archive directory by
            :mod:`configmaster.management.commands.archive_old_configs`.

        Args:
            url: Remote CMDB URL to connect to

        Example data (alphanumeric identifier)::

            {
              "C123": {
                "hostname": "c123.example.cpm",
                "name": "Edge firewall C123",
                "device_group": "Firewall"
               },
              "C124": {
                "hostname": "c124.example.cpm",
                "name": "Edge firewall C123",
                "device_group": "Firewall"
               }
            }

        Example data (FQDN as identifier)::

            {
              "core.example.com": {
                "hostname": "core.example.com",
                "name": "Core Router",
                "device_group": "Router"
               },
              "access01.example.com": {
                "hostname": "access01.example.com",
                "name": "Access Switch #1",
                "device_group": "Switch"
               }
            }

        """

        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
        else:
            self.stderr.write("Failed to connect to CMDB.")

    @staticmethod
    def fetch_cmdb_data_from_file(filename):
        """
        Read CMDB data from a file instead of downloading it.

        Args:
            filename (str): Local path

        Returns:
            See :meth:`fetch_cmdb_data` for data format.

        """
        return json.load(open(filename))

    def handle(self, *args, **options):
        if not options['filename']:
            if not settings.CMDB_EXPORT_URL:
                self.stderr.write("No CMDB_EXPORT_URL configured")
                return

            cmdb_export = self.fetch_cmdb_data(settings.CMDB_EXPORT_URL)
        else:
            cmdb_export = self.fetch_cmdb_data_from_file(options['filename'])

        for label, data in cmdb_export.iteritems():
            self.stdout.write("Processing %s..." % label)

            try:
                group = DeviceGroup.objects.get(name=data['device_group'])
            except DeviceGroup.DoesNotExist:
                self.stderr.write(
                    "Group %s does not exist" % data['device_group'])
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
                    self.stdout.write(
                        "Device %s out of service, deleting..." % label)
                    device.delete()
                    continue

            device.group = group
            device.name = data['name']
            device.hostname = data['hostname']
            device.sync = True

            device.save()

        call_command(
            "archive_old_configs",
            stdout=self.stdout, stderr=self.stderr)