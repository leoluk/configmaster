import pytest

from django.core.management import call_command

from configmaster.models import Task, DeviceType, Device
from conftest import config


@pytest.mark.django_db
@pytest.mark.parametrize('juniper', config['junipers'])
def test_juniper_get_version(
        credential,
        connection_setting,
        device_group,
        juniper,
        label,
):
    task = Task(
        name='Config Compare',
        class_name='NetworkDeviceCompareWithStartupHandler'
    )
    task.save()

    hostname = juniper['hostname']
    expected_version = juniper['version']

    device_type = DeviceType(
        name='Juniper SSG',
        credential=credential,
        connection_setting=connection_setting,
        alternative_config_compare=True,
    )
    device_type.save()
    device_type.tasks.add(task)
    device = Device(
        label=label,
        hostname=hostname,
        group=device_group,
        device_type=device_type,
    )
    device.save()

    call_command('run', label)

    device.refresh_from_db()
    assert device.version_info == expected_version
