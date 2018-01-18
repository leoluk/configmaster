import pytest

from django.core.management import call_command

from configmaster.models import Device, Repository
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

    report = device.get_latest_report_for_task(backup_task)
    assert report.result_is_success()


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


@pytest.mark.django_db
@pytest.mark.parametrize('device_info', config['fortigates'])
def test_fortigate_no_backup_if_the_config_did_not_change(
        device_type_fortigate,
        device_group,
        backup_task,
        device_info,
):
    device_type = device_type_fortigate

    hostname = device_info['hostname']
    device_type.tasks.add(backup_task)
    device_type.checksum_config_compare = True
    device_type.save()
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
    # Since the config did not change, there should be no new commit
    with pytest.raises(AssertionError):
        _check_config_backup(
            device,
            config['repository']['path'],
        )


@pytest.mark.django_db
@pytest.mark.parametrize('device_info', config['fortigates'])
def test_fortigate_backup_also_fails_on_repeated_runs(
        device_type_fortigate,
        device_group,
        backup_task,
        device_info,
):
    from configmaster.management.handlers.config_backup import NetworkDeviceConfigBackupHandler

    device_type = device_type_fortigate
    device_type.tasks.add(backup_task)
    device_type.checksum_config_compare = True
    device_type.save()

    # Create a device with a non-existing repository to provoke an error
    wrong_repository = Repository(path='wrong_repository_path')
    wrong_repository.save()
    device_group.repository = wrong_repository
    device_group.save()
    hostname = device_info['hostname']
    device = Device(
        label=DUMMY_LABEL,
        hostname=hostname,
        group=device_group,
        device_type=device_type,
    )
    device.save()

    handler = NetworkDeviceConfigBackupHandler(device)

    # Run should fail because repository is not found
    with pytest.raises(OSError) as e:
        handler.run()
    assert 'No such file or directory' in str(e)

    # Second run should fail as well
    with pytest.raises(OSError) as e:
        handler.run()
    assert 'No such file or directory' in str(e)
