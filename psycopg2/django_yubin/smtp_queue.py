#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------


"""Queued SMTP email backend class."""

from django.core.mail.backends.base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    '''
    A wrapper that manages a queued SMTP system.

    '''

    def send_messages(self, email_messages):
        """
        Add new messages to the email queue.

        The ``email_messages`` argument should be one or more instances
        of Django's core mail ``EmailMessage`` class.

        The messages can be assigned a priority in the queue by including
        an 'X-Mail-Queue-Priority' header set to one of the option strings
        in models.PRIORITIES.

        """
        if not email_messages:
            return

        from django_yubin import queue_email_message

        num_sent = 0
        for email_message in email_messages:
            if queue_email_message(email_message):
                num_sent += 1
        return num_sent
