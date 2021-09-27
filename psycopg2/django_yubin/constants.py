#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

# Deprecated, keeped here for backward compatibility, use PRIORITY_NOW instead.
PRIORITY_EMAIL_NOW = 0

PRIORITY_NOW_NOT_QUEUED = -1
PRIORITY_NOW = 0
PRIORITY_HIGH = 1
PRIORITY_NORMAL = 3
PRIORITY_LOW = 5

RESULT_SENT = 0
RESULT_SKIPPED = 1
RESULT_FAILED = 2

PRIORITIES = {
    'now-not-queued': PRIORITY_NOW_NOT_QUEUED,
    'now': PRIORITY_NOW,
    'high': PRIORITY_HIGH,
    'normal': PRIORITY_NORMAL,
    'low': PRIORITY_LOW,
}

PRIORITY_HEADER = 'X-Mail-Queue-Priority'
