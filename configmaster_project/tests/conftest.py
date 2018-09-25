import os

import yaml
import pytest
from sh import git

from configmaster.models import (
    Credential,
    ConnectionSetting,
    DeviceGroup,
    DeviceType,
    Repository,
    Task,
)
from utils import cleanup_repo

config_path = os.path.join('configmaster_project', 'test_config.yaml')
with open(config_path) as f:
    config = yaml.load(f)


@pytest.mark.django_db
@pytest.fixture
def credential():
    username = config['credentials']['username']
    password = config['credentials']['password']

    credential = Credential(
        type=1,
        username=username,
        password=password,
        )
    credential.save()
    return credential


@pytest.fixture
def connection_setting():
    connection_setting = ConnectionSetting(
        name='standard',
        ssh_port=22,
    )
    connection_setting.save()
    return connection_setting




@pytest.fixture
def repository():
    repo_path = config['repository']['path']
    cleanup_repo(repo_path)
    repository = Repository(
        path=repo_path,
    )
    repository.id = 1
    repository.save()
    return repository


@pytest.fixture
def device_group(repository):
    device_group = DeviceGroup(
        name='FirewallOrSwitch',
        plural='FirewallsOrSwitches',
        repository=repository,
    )
    device_group.save()
    return device_group


@pytest.fixture
def device_type_fortigate(credential, connection_setting):
    device_type = DeviceType(
        name='Fortigate',
        version_regex='#config-version=(.+):opmode',
        credential=credential,
        connection_setting=connection_setting
    )
    device_type.save()
    return device_type


@pytest.fixture
def device_type_juniper(credential, connection_setting):
    device_type = DeviceType(
        name='Juniper SSG',
        credential=credential,
        connection_setting=connection_setting,
    )
    device_type.save()
    return device_type


@pytest.fixture
def device_type_procurve(credential, connection_setting):
    device_type = DeviceType(
        name='HP ProCurve',
        version_regex='; (.+) Configuration Editor; Created on release (.+)',
        credential=credential,
        connection_setting=connection_setting
    )
    device_type.save()
    return device_type


@pytest.fixture
def backup_task():
    backup_task = Task(
        name='Config Backup',
        class_name='NetworkDeviceConfigBackupHandler'
    )
    backup_task.save()
    return backup_task


@pytest.fixture
def ntp_task():
    ntp_task = Task(
        name='NTP',
        class_name='NetworkDeviceNTPHandler'
    )
    ntp_task.save()
    return ntp_task

@pytest.fixture
def label(request):
    """
    Returns a dummy label containing the name of the test.
    """
    test_name = request.node.name
    return 'label_for_' + test_name
