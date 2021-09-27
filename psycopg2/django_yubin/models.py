#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

from django.db import models
from django.utils.encoding import force_bytes
from django.utils.timezone import now
from django_yubin import constants, managers

from pyzmail.parse import message_from_string, message_from_bytes
from six import python_2_unicode_compatible


PRIORITIES = (
    (constants.PRIORITY_NOW, 'now'),
    (constants.PRIORITY_HIGH, 'high'),
    (constants.PRIORITY_NORMAL, 'normal'),
    (constants.PRIORITY_LOW, 'low'),
)

RESULT_CODES = (
    (constants.RESULT_SENT, 'success'),
    (constants.RESULT_SKIPPED, 'not sent (blacklisted or paused)'),
    (constants.RESULT_FAILED, 'failure'),
)


@python_2_unicode_compatible
class Message(models.Model):
    """
    An email message.

    The ``to_address``, ``from_address`` and ``subject`` fields are merely for
    easy of access for these common values. The ``encoded_message`` field
    contains the entire encoded email message ready to be sent to an SMTP
    connection.

    """
    to_address = models.CharField(max_length=200)
    from_address = models.CharField(max_length=200)
    subject = models.CharField(max_length=255)

    encoded_message = models.TextField()
    date_created = models.DateTimeField(default=now)
    date_sent = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('date_created',)

    def __str__(self):
        return '%s: %s' % (self.to_address, self.subject)

    def get_pyz_message(self):
        try:
            msg = message_from_string(self.encoded_message)
        except UnicodeEncodeError:
            msg = message_from_string(force_bytes(self.encoded_message))
        except (TypeError, AttributeError):
            msg = message_from_bytes(self.encoded_message)
        return msg


class QueuedMessage(models.Model):
    """
    A queued message.

    Messages in the queue can be prioritised so that the higher priority
    messages are sent first (secondarily sorted by the oldest message).

    """
    message = models.OneToOneField(Message, editable=False, on_delete=models.CASCADE)
    priority = models.PositiveSmallIntegerField(choices=PRIORITIES,
                                                default=constants.PRIORITY_NORMAL)
    deferred = models.DateTimeField(null=True, blank=True)
    retries = models.PositiveIntegerField(default=0)
    date_queued = models.DateTimeField(default=now)

    objects = managers.QueueManager()

    class Meta:
        ordering = ('priority', 'date_queued')

    def defer(self):
        self.deferred = now()
        self.save()


class Blacklist(models.Model):
    """
    A blacklisted email address.

    Messages attempted to be sent to e-mail addresses which appear on this
    blacklist will be skipped entirely.

    """
    email = models.EmailField(max_length=200)
    date_added = models.DateTimeField(default=now)

    class Meta:
        ordering = ('-date_added',)
        verbose_name = 'blacklisted e-mail address'
        verbose_name_plural = 'blacklisted e-mail addresses'


class Log(models.Model):
    """
    A log used to record the activity of a queued message.

    """
    message = models.ForeignKey(Message, editable=False, on_delete=models.CASCADE)
    result = models.PositiveSmallIntegerField(choices=RESULT_CODES)
    date = models.DateTimeField(default=now)
    log_message = models.TextField()

    class Meta:
        ordering = ('-date',)
