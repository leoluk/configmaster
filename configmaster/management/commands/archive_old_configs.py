import os

from django.core.management.base import BaseCommand
from configmaster.management.handlers.config_backup import \
    NetworkDeviceConfigBackupHandler
from configmaster.models import Device, DeviceGroup

from sh import git


class Command(BaseCommand):
    def handle(self, *args, **options):
        for group in DeviceGroup.objects.all():
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