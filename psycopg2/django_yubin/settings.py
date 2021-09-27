#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

from django.conf import settings
from django_yubin import constants

# Provide a way of temporarily pausing the sending of mail.
PAUSE_SEND = getattr(settings, "MAILER_PAUSE_SEND", False)

USE_BACKEND = getattr(settings, 'MAILER_USE_BACKEND',
                      'django.core.mail.backends.smtp.EmailBackend')

# Default priorities for the mail_admins and mail_managers methods.
MAIL_ADMINS_PRIORITY = getattr(settings, 'MAILER_MAIL_ADMINS_PRIORITY',
                               constants.PRIORITY_HIGH)
MAIL_MANAGERS_PRIORITY = getattr(settings, 'MAILER_MAIL_MANAGERS_PRIORITY',
                                 None)

# When queue is empty, how long to wait (in seconds) before checking again.
EMPTY_QUEUE_SLEEP = getattr(settings, "MAILER_EMPTY_QUEUE_SLEEP", 30)

# Lock timeout value. how long to wait for the lock to become available.
# default behavior is to never wait for the lock to be available.
LOCK_WAIT_TIMEOUT = max(getattr(settings, "MAILER_LOCK_WAIT_TIMEOUT", 0), 0)

# An optional alternate lock path, potentially useful if you have multiple
# projects running on the same server.
LOCK_PATH = getattr(settings, "MAILER_LOCK_PATH", None)

# When MAILER_TEST_MODE is True, recipient addresses of all messages are replaced with
# the email addresses set in MAILER_TEST_EMAIL before being sent
MAILER_TEST_MODE = getattr(settings, "MAILER_TEST_MODE", False)
MAILER_TEST_EMAIL = getattr(settings, "MAILER_TEST_EMAIL", '')

MAILER_HC_QUEUED_LIMIT_OLD = getattr(settings, "MAILER_HC_QUEUED_LIMIT_OLD", 30)
