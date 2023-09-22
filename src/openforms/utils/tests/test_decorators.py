from django import forms
from django.contrib.admin.widgets import AdminTextInputWidget
from django.db import models
from django.test import SimpleTestCase
from django.test.client import RequestFactory

import requests

from openforms.utils.decorators import supress_requests_errors


class DbFieldsExceptionHandlerTests(SimpleTestCase):
    def setUp(self):
        self.db_field = models.CharField(
            "db field",
            blank=True,
            help_text="help text",
        )

        self.request = RequestFactory().get("/test")

    def test_no_exception_detected(self):
        @supress_requests_errors(fields=["db field"])
        class TestClass:
            formfield_overrides = {models.CharField: {"widget": AdminTextInputWidget}}

            def formfield_for_dbfield(self, db_field, request, **kwargs):
                return forms.CharField(
                    label="db field",
                    help_text="help text",
                )

        form_field = TestClass.formfield_for_dbfield(
            TestClass, db_field=self.db_field, request=self.request
        )

        self.assertIsInstance(form_field, forms.CharField)
        self.assertNotIn(
            "Could not load data - enable and check the request logs for more details",
            form_field.widget.render("db field", None),
        )

    def test_trigger_exception(self):
        @supress_requests_errors(fields=["db field"])
        class TestClass:
            formfield_overrides = {models.CharField: {"widget": AdminTextInputWidget}}

            def formfield_for_dbfield(self, db_field, request, **kwargs):
                raise requests.exceptions.RequestException()

        form_field = TestClass.formfield_for_dbfield(
            TestClass, db_field=self.db_field, request=self.request
        )

        self.assertIsInstance(form_field, forms.CharField)
        self.assertIn(
            "Could not load data - enable and check the request logs for more details",
            form_field.widget.render("db field", None),
        )

    def test_raising_error_for_crashing_fields_that_are_not_provided(self):
        @supress_requests_errors()
        class TestClass:
            formfield_overrides = {models.CharField: {"widget": AdminTextInputWidget}}

            def formfield_for_dbfield(self, db_field, request, **kwargs):
                raise requests.exceptions.RequestException()

        with self.assertRaises(requests.exceptions.RequestException):
            TestClass.formfield_for_dbfield(
                TestClass, db_field=self.db_field, request=self.request
            )
