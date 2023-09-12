from django import forms
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import models
from django.test import SimpleTestCase
from django.test.client import RequestFactory

import requests
import zds_client

from openforms.utils.decorators import dbfields_exception_handler


class DbFieldsExceptionHandlerTests(SimpleTestCase):
    def setUp(self):
        self.db_field = models.CharField(
            "db field",
            blank=True,
            help_text="help text",
        )

        self.request = RequestFactory().get("/test")

        # setup django.messages
        setattr(self.request, "session", "session")
        messages = FallbackStorage(self.request)
        setattr(self.request, "_messages", messages)

    def test_no_exception_detected(self):
        @dbfields_exception_handler(exceptions=(Exception))
        def formfield_for_dbfield(db_field, request):
            return forms.CharField(
                label="db field",
                help_text="help text",
            )

        form_field = formfield_for_dbfield(self.db_field, self.request)

        messages = (m.message for m in get_messages(self.request))
        self.assertTrue(not any(messages))
        self.assertIsInstance(form_field, forms.CharField)

    def test_trigger_exception(self):
        @dbfields_exception_handler(exceptions=(requests.exceptions.RequestException,))
        def formfield_for_dbfield(db_field, request):
            raise requests.exceptions.RequestException()

        form_field = formfield_for_dbfield(self.db_field, self.request)
        messages = [m.message for m in get_messages(self.request)]
        self.assertEqual(
            messages,
            [
                "Could not load data for field 'db field' - enable and check the request logs for more details",
            ],
        )
        self.assertIsInstance(form_field, forms.CharField)

    def test_raising_not_given_exception(self):
        @dbfields_exception_handler(exceptions=(requests.exceptions.RequestException,))
        def formfield_for_dbfield(db_field, request):
            raise zds_client.ClientError()

        with self.assertRaises(zds_client.ClientError):
            formfield_for_dbfield(self.db_field, self.request)
        messages = (m.message for m in get_messages(self.request))
        self.assertTrue(not any(messages))
