from django.core.management import BaseCommand
import re
import traceback
from configmaster.management import handlers
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
            elif not device.enabled:
                self.stdout.write("Device %s is disabled, skipping..." % device.label)
                continue
            else:
                self.stdout.write("Processing %s..." % device.label)

            try:
                if RE_MATCH_SINGLE_WORD.match(device.device_type.handler):
                    handler = getattr(handlers, device.device_type.handler)(device)
                    result, output = handler.run()
                elif not device.device_type.handler:
                    raise ValueError("Empty handler")
                else:
                    raise ValueError("Invalid class name: %s" % device.device_type.handler)

            except Exception:
                result = Report.RESULT_FAILURE
                output = traceback.format_exc()

            if result == Report.RESULT_FAILURE:
                self.stderr.write("Device %s failed: %s" % (device.label, output))
            else:
                self.stdout.write("Device %s succeeded" % device.label)

            report = Report()
            report.device = device
            report.result = result
            report.output = output
            report.save()




