# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...messages import BasicHTMLEmailMessageView


class Command(BaseCommand):
    help = 'Send a simple email in order to check connection parameters.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--subject',
            dest='subject',
            default='Hello World',
            help='Email subject.',
        )

        parser.add_argument(
            '-c',
            '--content',
            dest='content',
            default='Hello World',
            help='Email content.',
        )

        parser.add_argument(
            '-t',
            '--to',
            dest='to',
            default='',
            help='Email address to send message.',
        )

    def handle(self, *args, **options):
        from_email = settings.DEFAULT_FROM_EMAIL
        to = options['to']
        if to:
            to_list = [to]
        else:
            to_list = [x[1] for x in settings.ADMINS if len(x) > 0]

        if not to_list:
            raise CommandError('Please provide an email address or set a valid settings.ADMINS configuration')

        subject = options['subject']
        content = options['content']
        message = BasicHTMLEmailMessageView(subject, content)
        message.send(from_email=from_email, to=to_list)

        # This output is checked in tests.
        self.stdout.write('Created email(s): 1')
