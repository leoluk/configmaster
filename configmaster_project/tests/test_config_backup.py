import pytest

from django.core.management import call_command

from configmaster.models import Device
from .utils import get_last_commit_message, get_last_commit_id
from conftest import config, DUMMY_LABEL


def _check_new_commit(last_commit_id, repository_path, device):
    """
    Verifies that there is a new commit with the expected commit message.
    """
    current_commit_id = get_last_commit_id(repository_path)
    # There should be a new commit.
    assert last_commit_id != current_commit_id

    commit_message = get_last_commit_message(repository_path)
    expected_commit_message = (
        '{group_name} config change on {label} ({hostname})'.format(
            group_name=device.group.name,
            label=device.label,
            hostname=device.hostname,
        )
    )
    assert commit_message == expected_commit_message
    return current_commit_id


def _check_config_backup(
        device,
        repository_path,
        expected_version=None,
):
    last_commit_id = get_last_commit_id(repository_path)
    call_command('run', device.label)
    device.refresh_from_db()
    if expected_version is not None:
        assert device.version_info[:len(expected_version)] == expected_version
    _check_new_commit(last_commit_id, repository_path, device)


@pytest.mark.django_db
@pytest.mark.parametrize('device_info', config['fortigates'])
def test_fortigate_config_backup(
        device_type_fortigate,
        device_group,
        backup_task,
        device_info,
):
    device_type = device_type_fortigate

    hostname = device_info['hostname']
    device_type.tasks.add(backup_task)
    device = Device(
        label=DUMMY_LABEL,
        hostname=hostname,
        group=device_group,
        device_type=device_type,
    )
    device.save()

    _check_config_backup(
        device,
        config['repository']['path'],
        device_info['version'],
    )


@pytest.mark.django_db
@pytest.mark.parametrize('device_info', config['junipers'])
def test_juniper_config_backup(
        device_type_juniper,
        device_group,
        backup_task,
        device_info,
):
    device_type = device_type_juniper
    device_type.tasks.add(backup_task)
    device = Device(
        label=DUMMY_LABEL,
        hostname=device_info['hostname'],
        group=device_group,
        device_type=device_type,
    )
    device.save()
    
    # The version is retrieved with the config compare task
    _check_config_backup(
        device,
        config['repository']['path'],
    )


@pytest.mark.django_db
@pytest.mark.parametrize('device_info', config['procurves'])
def test_procurve_config_backup(
        device_type_procurve,
        device_group,
        backup_task,
        device_info,
):
    device_type = device_type_procurve
    device_type.tasks.add(backup_task)
    device = Device(
        label=DUMMY_LABEL,
        hostname=device_info['hostname'],
        group=device_group,
        device_type=device_type,
    )
    device.save()

    _check_config_backup(
        device,
        config['repository']['path'],
        device_info['version'],
    )
