#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from configmaster.models import Report


class Command(BaseCommand):
    """
    Removes reports older than 7 days.

    Warning:
        In a production environment, this management command must be
        periodically invoked by a cronjob, or the database will fill up over
        time.

    """
    help = "Removes all reports older than 7 days."

    def handle(self, *args, **options):
        Report.objects.filter(
            date__lte=timezone.now() - datetime.timedelta(
                days=7)).delete()
