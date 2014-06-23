from django.core.management import BaseCommand
import re
import traceback
from configmaster.management import handlers
from configmaster.management.handlers.base import TaskExecutionError
from configmaster.models import Device, Report

RE_MATCH_SINGLE_WORD = re.compile(r'\A[\w-]+\Z')


class Command(BaseCommand):
    help = "Config management run"

    # noinspection PyBroadException
    def handle(self, *args, **options):
        for device in Device.objects.all():
            if device.device_type is None:
                self.stdout.write("Device %s has no device type, skipping..." % device.label)
                continue
            elif (not device.enabled) or (not device.group.enabled):
                self.stdout.write("Device %s is disabled, skipping..." % device.label)
                continue
            else:
                if not device.device_type.tasks.count():
                    self.stdout.write("No tasks for %s" % device.label)
                    continue

                self.stdout.write("Processing %s..." % device.label)

                for task in device.device_type.tasks.all():
                    try:
                        if RE_MATCH_SINGLE_WORD.match(task.class_name):
                            handler_obj = getattr(handlers, task.class_name)(device)
                            _result = handler_obj.run()
                            if _result is None:
                                raise RuntimeError("Task handler did not return any data")
                            result, output = _result
                        elif not task.class_name:
                            raise ValueError("Empty class name")
                        else:
                            raise ValueError("Invalid class name: %s" % device.device_type.handler)

                    except TaskExecutionError, e:
                        result = Report.RESULT_FAILURE
                        output = str(e)
                    except Exception:
                        result = Report.RESULT_FAILURE
                        output = traceback.format_exc()

                    if result == Report.RESULT_FAILURE:
                        self.stderr.write('Device %s, task "%s" failed: %s' % (device.label, task.name, output))
                    else:
                        self.stdout.write('Device %s, task "%s" succeeded' % (device.label, task.name))
                        self.stdout.write("Output: %r" % output)

                    report = Report()
                    report.device = device
                    report.result = result
                    report.task = task
                    report.output = output
                    report.save()
