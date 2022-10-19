from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import UserFactory

from ..constants import AuthAttribute
from .factories import AuthInfoFactory, RegistratorInfoFactory


class AuthInfoAdminValidationTest(WebTest):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(is_superuser=True, is_staff=True, app=self.app)

    @override_settings(LANGUAGE_CODE="en")
    def test_validate_invalid_bsn(self):
        auth_info_bsn = AuthInfoFactory.create()

        response = self.app.get(
            reverse(
                "admin:of_authentication_authinfo_change", args=(auth_info_bsn.pk,)
            ),
            user=self.user,
        )
        form = response.forms["authinfo_form"]
        form["value"] = "invalid-bsn"

        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(form_response, "Expected a numerical value.", html=True)

    @override_settings(LANGUAGE_CODE="nl")
    def test_validate_invalid_kvk(self):
        auth_info_kvk = AuthInfoFactory.create(attribute=AuthAttribute.kvk)

        response = self.app.get(
            reverse(
                "admin:of_authentication_authinfo_change", args=(auth_info_kvk.pk,)
            ),
            user=self.user,
        )
        form = response.forms["authinfo_form"]
        form["value"] = "123456789"

        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(
            form_response, "KvK-nummer moet 8 tekens lang zijn.", html=True
        )


class RegistratorInfoAdminValidationTest(WebTest):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(is_superuser=True, is_staff=True, app=self.app)

    @override_settings(LANGUAGE_CODE="en")
    def test_validate_invalid_bsn(self):
        auth_info_bsn = RegistratorInfoFactory.create(attribute=AuthAttribute.bsn)

        response = self.app.get(
            reverse(
                "admin:of_authentication_registratorinfo_change",
                args=(auth_info_bsn.pk,),
            ),
            user=self.user,
        )
        form = response.forms["registratorinfo_form"]
        form["value"] = "invalid-bsn"

        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(form_response, "Expected a numerical value.", html=True)

    @override_settings(LANGUAGE_CODE="nl")
    def test_validate_invalid_kvk(self):
        auth_info_kvk = RegistratorInfoFactory.create(attribute=AuthAttribute.kvk)

        response = self.app.get(
            reverse(
                "admin:of_authentication_registratorinfo_change",
                args=(auth_info_kvk.pk,),
            ),
            user=self.user,
        )
        form = response.forms["registratorinfo_form"]
        form["value"] = "123456789"

        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(
            form_response, "KvK-nummer moet 8 tekens lang zijn.", html=True
        )
