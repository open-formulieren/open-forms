# encoding: utf-8

import datetime
import logging

from django.core.management.base import BaseCommand

from django_yubin.management.commands import create_handler
from django_yubin.models import Message


class Command(BaseCommand):
    help = 'Delete the mails created before -d days (default 90)'

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--days',
            dest='days',
            type=int,
            default=90,
            help="Cleanup mails older than this many days, defaults to 90.",
        )

    def handle(self, verbosity, **options):
        # Delete mails and their related logs and queued created before X days
        logger = logging.getLogger('django_yubin')
        handler = create_handler(verbosity)
        logger.addHandler(handler)

        today = datetime.date.today()
        cutoff_date = today - datetime.timedelta(options['days'])
        count = Message.objects.filter(date_created__lt=cutoff_date).count()
        if count:
            Message.objects.filter(date_created__lt=cutoff_date).delete()
            logger.info("Deleted %s mails created before %s " %
                        (count, cutoff_date))
