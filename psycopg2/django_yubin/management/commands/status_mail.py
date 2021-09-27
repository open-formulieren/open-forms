# encoding: utf-8

"""
This command returns the status of the queue in the format:
    queued/deferred/seconds

where:
    queued      is the number of queued messages we have actually
    deferred    number of deferred messages we have actually
    seconds     age in seconds of the oldest messages

Example:

    2/0/10

means we have 2 queued messages, 0 defered messaged and than the oldest message
in the queue is just 2 seconds old.
"""
from __future__ import unicode_literals

import json

from django.core.management.base import BaseCommand
from django_yubin.models import QueuedMessage
from django.utils.timezone import now


class Command(BaseCommand):
    help = "Returns a string with the queue status as queued/deferred/seconds"

    def add_arguments(self, parser):
        parser.add_argument('--json-format', action='store_true',
                            help='Allows to return the response as a json format.')

    def handle(self, *args, **kwargs):
        # If this is just a count request the just calculate, report and exit.
        queued = QueuedMessage.objects.non_deferred().count()
        deferred = QueuedMessage.objects.deferred().count()
        try:
            oldest = QueuedMessage.objects.non_deferred().order_by(
                'date_queued')[0]
            seconds = (now() - oldest.date_queued).seconds
        except (IndexError, QueuedMessage.DoesNotExist):
            seconds = 0

        # This output is checked in tests.
        if kwargs['json_format']:
            self.stdout.write(json.dumps({
                'queued': queued,
                'deferred': deferred,
                'seconds': seconds,
            }))
        else:
            self.stdout.write('%s/%s/%s\n' % (queued, deferred, seconds))
