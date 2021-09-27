# encoding: utf-8

import logging

from django.core.management.base import BaseCommand
from django.db import connection
from django_yubin import models
from django_yubin.management.commands import create_handler


class Command(BaseCommand):
    help = 'Place deferred messages back in the queue.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-m',
            '--max-retries',
            dest='max_retries',
            type=int,
            default=0,
            help="Don't reset deferred messages with more than this many "
                 "retries.",
        )

    def handle(self, verbosity, **options):
        # Send logged messages to the console.
        logger = logging.getLogger('django_yubin')
        handler = create_handler(verbosity)
        logger.addHandler(handler)

        count = models.QueuedMessage.objects.retry_deferred(
                                            max_retries=options['max_retries'])
        logger = logging.getLogger('django_yubin.commands.retry_deferred')
        if count:
            logger.info("%s deferred message%s placed back in the queue" %
                        (count, count != 1 and 's' or ''))

        logger.removeHandler(handler)
        connection.close()
