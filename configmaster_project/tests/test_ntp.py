import pytest
from django.core.management import call_command
from django.conf import settings

from configmaster.models import Device, Report
from conftest import config


def _check_ntp(device):
    old_ntp_max_delta = settings.CONFIGMASTER_NTP_MAX_DELTA
    try:
        call_command('run', device.label)
        latest_report = Report.objects\
            .filter(device=device)\
            .order_by('-date')[0]
        assert latest_report.result_is_success() == True

        settings.CONFIGMASTER_NTP_MAX_DELTA = 0
        call_command('run', device.label)

        latest_report = Report.objects\
            .filter(device=device)\
            .order_by('-date')[0]
        assert latest_report.result_is_success() == False
    finally:
        settings.CONFIGMASTER_NTP_MAX_DELTA = old_ntp_max_delta


@pytest.mark.django_db
@pytest.mark.parametrize(
    'device_info', config['junipers'],
)
def test_ntp_juniper(
        device_type_juniper,
        ntp_task,
        device_info,
        device_group,
        label,
):
    device_type = device_type_juniper
    hostname = device_info['hostname']

    device_type.tasks.add(ntp_task)
    device = Device(
        label=label,
        hostname=hostname,
        group=device_group,
        device_type=device_type,
    )
    device.save()
    _check_ntp(device)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'device_info', config['fortigates'],
)
def test_ntp_fortigate(
        device_type_fortigate,
        ntp_task,
        device_info,
        device_group,
        label,
):
    device_type = device_type_fortigate
    hostname = device_info['hostname']

    device_type.tasks.add(ntp_task)
    device = Device(
        label=label,
        hostname=hostname,
        group=device_group,
        device_type=device_type,
    )
    device.save()
    _check_ntp(device)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'device_info', config['procurves'],
)
def test_ntp_procurve(
        device_type_procurve,
        ntp_task,
        device_info,
        device_group,
        label,
):
    device_type = device_type_procurve
    hostname = device_info['hostname']

    device_type.tasks.add(ntp_task)
    device = Device(
        label=label,
        hostname=hostname,
        group=device_group,
        device_type=device_type,
    )
    device.save()
    _check_ntp(device)
