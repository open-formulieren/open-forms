#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

import hashlib


def unimplemented(*args, **kwargs):
    raise NotImplementedError


class Attachment(object):
    """
    Utility class to contain the attachment information
    """

    def __init__(self, mailpart):
        self.filename = mailpart.sanitized_filename
        self.tipus = mailpart.type
        self.charset = mailpart.charset
        self.content_description = mailpart.part.get('Content-Description')
        self.payload = mailpart.get_payload()
        self.length = len(self.payload)
        self.firma = hashlib.md5(self.payload).hexdigest()


def get_attachments(msg):
    """
    Returns a list with all the mail attachments
    """

    attachments = []
    for mailpart in msg.mailparts:
        if not mailpart.is_body and mailpart.disposition == 'attachment':
            attachment = Attachment(mailpart)
            attachments.append(attachment)
    return attachments


def get_attachment(msg, key):
    """
    Given a msg returns the attachment who's signature (md5 key) matches
    the key value
    """

    for mailpart in msg.mailparts:
        if not mailpart.is_body and mailpart.disposition == 'attachment':
            attachment = Attachment(mailpart)
            if attachment.firma == key:
                return attachment
    return None
