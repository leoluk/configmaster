import datetime

from django.core.management.base import BaseCommand

from configmaster.models import Report


class Command(BaseCommand):
    def handle(self, *args, **options):
        Report.objects.filter(
            date__lte=datetime.datetime.today() - datetime.timedelta(
                days=7)).delete()