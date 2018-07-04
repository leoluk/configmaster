from configmaster.models import Device, Task, Report


def test_device_status_api_view(admin_client, device_group):
    device_label = 'AA00'
    device = Device(label=device_label, group=device_group)
    device.save()

    task_id = 5
    task = Task(id=task_id)
    task.save()

    report = Report(
        device=device,
        task=task,
        result=Report.RESULT_FAILURE,
        output='error',
        long_output='There was an error.'
    )
    report.save()

    url = '/api/device_status?task={}&device={}'.format(
        str(task_id),
        device_label,
    )
    response = admin_client.get(url)

    assert response.status_code == 200
    assert 'There was an error.' in response.content
