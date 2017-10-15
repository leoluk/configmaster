#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

"""
This management command is called at the end of each run and moves config
files for devices which are no longer in the database to an ``_Archive`` folder.

You do not need to run this command from the command line.

"""

import os
from django.core.management.base import BaseCommand
from sh import git

from configmaster.management.handlers.config_backup import \
    NetworkDeviceConfigBackupHandler
from configmaster.models import Device, DeviceGroup


class Command(BaseCommand):
    def handle(self, *args, **options):
        for group in DeviceGroup.objects.all():
            if group.repository is None:
                continue

            repo_path, group_path = os.path.split(group.config_backup_path)
            archive_path = os.path.join(repo_path, "_Archive", group_path)

            if not os.path.exists(group.config_backup_path):
                self.stderr.write("Invalid path: %s" % group.config_backup_path)
                continue

            group.repository.lock.acquire()

            if not os.path.exists(archive_path):
                os.makedirs(archive_path)

            os.chdir(group.config_backup_path)

            for filename in os.listdir("."):
                label = os.path.splitext(filename)[0]
                try:
                    Device.objects.get(label=label)
                except Device.DoesNotExist:
                    self.stdout.write("Archiving: %s" % label)
                    os.rename(filename, os.path.join(archive_path, filename))

            os.chdir(group.repository.path)

            git.add("-A", ".")

            if NetworkDeviceConfigBackupHandler._git_commit(
                "Moving device configs to archive"):
                git.push()

            group.repository.lock.release()