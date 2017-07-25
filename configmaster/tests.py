#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

import os

from django.test import TestCase
from django.core.management import call_command
from sh import cd, git
import yaml

from .models import Device, DeviceGroup, DeviceType, Repository, Credential, Task, ConnectionSetting

with open('test_config.yaml') as f:
    config = yaml.load(f)


def get_last_commit_message(repository_path):
    os.chdir(repository_path)
    return str(git('log', '-1', '--format=%B', _tty_out=False)).strip()


def get_last_commit_id(repository_path):
    os.chdir(repository_path)
    return str(git('log', '-1', '--format=%H', _tty_out=False)).strip()


class BaseTestSetup(TestCase):
     def setUp(self):
        username = config['credentials']['username']
        password = config['credentials']['password']
        repo_path = config['repository']['path']

        self.credential = Credential(
            type=1,
            username=username,
            password=password,
        )
        self.credential.save()

        self.connection_setting = ConnectionSetting(
            name='standard',
            ssh_port=22,
        )
        self.connection_setting.save()

        self.repository = Repository(
            path=repo_path,
        )
        self.repository.save()

        self.device_group = DeviceGroup(
            name='FirewallOrSwitch',
            plural='FirewallsOrSwitches',
            repository=self.repository,
        )
        self.device_group.save()


class TestConfigCompare(BaseTestSetup):
    def setUp(self):
        self.task = Task(
            name='Config Compare',
            class_name='NetworkDeviceCompareWithStartupHandler'
        )
        self.task.save()
        super(TestConfigCompare, self).setUp()

    def test_juniper_get_version(self):
        for juniper in config['junipers']:
            hostname = juniper['hostname']
            expected_version = juniper['version']

            device_type = DeviceType(
                name='Juniper SSG',
                credential=self.credential,
                connection_setting=self.connection_setting,
                alternative_config_compare=True,
            )
            device_type.save()
            device_type.tasks.add(self.task)
            device = Device(
                label='AA00',
                hostname=hostname,
                group=self.device_group,
                device_type=device_type,
            )
            device.save()

            call_command('run', 'AA00')

            device = Device.objects.get(label=device.label)
            self.assertEqual(device.version_info, expected_version)


class TestConfigBackup(BaseTestSetup):
    def setUp(self):
        self.backup_task = Task(
            name='Config Backup',
            class_name='NetworkDeviceConfigBackupHandler'
        )
        self.backup_task.save()
        super(TestConfigBackup, self).setUp()

    def test_fortigate_config_backup(self):
        for fortigate in config['fortigates']:
            hostname = fortigate['hostname']
            expected_version = fortigate['version']

            device_type = DeviceType(
                name='Fortigate',
                version_regex='#config-version=(.+):opmode',
                credential=self.credential,
                connection_setting=self.connection_setting
            )
            device_type.save()
            device_type.tasks.add(self.backup_task)
            device = Device(
                label='AA00',
                hostname=hostname,
                group=self.device_group,
                device_type=device_type,
            )
            device.save()
            last_commit_id = get_last_commit_id(self.repository.path)

            call_command('run', 'AA00')

            device = Device.objects.get(label=device.label)
            self.assertEqual(device.version_info, expected_version)
            self._check_new_commit(last_commit_id, device)

    def test_juniper_config_backup(self):
        for juniper in config['junipers']:
            hostname = juniper['hostname']

            device_type = DeviceType(
                name='Juniper SSG',
                credential=self.credential,
                connection_setting=self.connection_setting,
            )
            device_type.save()
            device_type.tasks.add(self.backup_task)

            device = Device(
                label='AA00',
                hostname=hostname,
                group=self.device_group,
                device_type=device_type,
            )
            device.save()
            last_commit_id = get_last_commit_id(self.repository.path)
            call_command('run', 'AA00')
            self._check_new_commit(last_commit_id, device)

    def test_procurve_config_backup(self):
         for procurve in config['procurves']:
            hostname = procurve['hostname']
            expected_version = procurve['version']

            device_type = DeviceType(
                name='HP ProCurve',
                version_regex='; (.+) Configuration Editor; Created on release (.+)',
                credential=self.credential,
                connection_setting=self.connection_setting
            )
            device_type.save()
            device_type.tasks.add(self.backup_task)

            device = Device(
                label='AA00',
                hostname=hostname,
                group=self.device_group,
                device_type=device_type,
            )
            device.save()
            last_commit_id = get_last_commit_id(self.repository.path)

            call_command('run', 'AA00')

            device = Device.objects.get(label=device.label)
            self.assertEqual(device.version_info, expected_version)
            self._check_new_commit(last_commit_id, device)

    def _check_new_commit(self, last_commit_id, device):
        """
        Verifies that there is a new commit with the expected commit message.
        """
        current_commit_id = get_last_commit_id(self.repository.path)
        # There should be a new commit.
        self.assertNotEqual(last_commit_id, current_commit_id)

        commit_message = get_last_commit_message(self.repository.path)
        expected_commit_message = '{group_name} config change on {label} ({hostname})'.format(
            group_name=device.group.name,
            label=device.label,
            hostname=device.hostname,
        )
        self.assertEqual(commit_message, expected_commit_message)
        return current_commit_id

