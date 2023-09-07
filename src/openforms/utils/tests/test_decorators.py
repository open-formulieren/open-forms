from django import forms
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.test import RequestFactory, SimpleTestCase
from django.utils.translation import gettext as _

import requests

from openforms.accounts.models import User
from openforms.admin.decorators import suppress_requests_errors


@suppress_requests_errors(User, fields=["first_name"])
class TestAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in ["first_name", "last_name"]:
            raise requests.RequestException

        return super().formfield_for_dbfield(db_field, request, **kwargs)


class DbFieldsExceptionHandlerTests(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get("/test")

    def test_none_crashing_field(self):
        model_admin = TestAdmin(User, AdminSite(name="test"))

        formfield = model_admin.formfield_for_dbfield(
            User._meta.get_field("username"), self.request
        )

        self.assertIsInstance(formfield, forms.CharField)
        self.assertHTMLEqual(
            formfield.widget.render("username", None),
            '<input class="vTextField" maxlength="150" name="username" type="text">',
        )

    def test_crashing_field_that_is_in_suppress_requests_errors_field_params(
        self,
    ):
        model_admin = TestAdmin(User, AdminSite(name="test"))

        formfield = model_admin.formfield_for_dbfield(
            User._meta.get_field("first_name"), self.request
        )

        self.assertIsInstance(formfield, forms.CharField)
        self.assertIn(
            _(
                "Could not load data - enable and check the request logs for more details."
            ),
            formfield.widget.render("first_name", None),
        )

    def test_crashing_field_that_is_not_in_suppress_requests_errors_field_params(
        self,
    ):
        model_admin = TestAdmin(User, AdminSite(name="test"))

        with self.assertRaises(requests.exceptions.RequestException):
            model_admin.formfield_for_dbfield(
                User._meta.get_field("last_name"), self.request
            )
