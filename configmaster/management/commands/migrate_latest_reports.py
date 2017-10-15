#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.core.management.base import BaseCommand
from configmaster.models import Device


class Command(BaseCommand):
    """
    Recalculate the latest_reports cache for all devices.

    Debugging command.
    """

    def handle(self, *args, **options):
        for device in Device.objects.all():
            latest_reports = device._latest_reports
            if not latest_reports:
                continue

            for task, status, report in latest_reports:
                if not report:
                    continue
                try:
                    report.result_url = report._result_url
                    report.save()
                except AttributeError:
                    pass
                device.remove_latest_reports_for_task(task)
                device.latest_reports.add(report)
                device.save()