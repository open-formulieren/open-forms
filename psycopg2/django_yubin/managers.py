#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

from django.db import models
from django_yubin import constants

try:
    from django.utils.timezone import now
except ImportError:
    import datetime
    now = datetime.datetime.now


class QueueMethods(object):
    """
    A mixin which provides extra methods to a QuerySet/Manager subclass.

    """

    def exclude_future(self):
        """
        Exclude future time-delayed messages.

        """
        return self.exclude(date_queued__gt=now())

    def now_priority(self):
        """
        Return a QuerySet of now priority queued messages.

        """
        return self.filter(priority=constants.PRIORITY_NOW)

    def high_priority(self):
        """
        Return a QuerySet of high priority queued messages.

        """
        return self.filter(priority=constants.PRIORITY_HIGH)

    def normal_priority(self):
        """
        Return a QuerySet of normal priority queued messages.

        """
        return self.filter(priority=constants.PRIORITY_NORMAL)

    def low_priority(self):
        """
        Return a QuerySet of low priority queued messages.

        """
        return self.filter(priority=constants.PRIORITY_LOW)

    def non_deferred(self):
        """
        Return a QuerySet containing all non-deferred queued messages,
        excluding "future" messages.

        """
        return self.exclude_future().filter(deferred=None)

    def deferred(self):
        """
        Return a QuerySet of all deferred messages in the queue, excluding
        "future" messages.

        """
        return self.exclude_future().exclude(deferred=None)


class QueueQuerySet(QueueMethods, models.query.QuerySet):
    pass


class QueueManager(QueueMethods, models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return QueueQuerySet(self.model, using=self._db)

    def retry_deferred(self, max_retries=None, new_priority=None):
        """
        Reset the deferred flag for all deferred messages so they will be
        retried.

        If ``max_retries`` is set, deferred messages which have been retried
        more than this many times will *not* have their deferred flag reset.

        If ``new_priority`` is ``None`` (default), deferred messages retain
        their original priority level. Otherwise all reset deferred messages
        will be set to this priority level.

        """
        queryset = self.deferred()
        if max_retries:
            queryset = queryset.filter(retries__lte=max_retries)
        count = queryset.count()
        update_kwargs = dict(deferred=None, retries=models.F('retries')+1)
        if new_priority is not None:
            update_kwargs['priority'] = new_priority
        queryset.update(**update_kwargs)
        return count
