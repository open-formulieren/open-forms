from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory

from ..constants import AuthAttribute
from .factories import AuthInfoFactory, RegistratorInfoFactory


@disable_admin_mfa()
class AuthInfoAdminValidationTest(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

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


@disable_admin_mfa()
class RegistratorInfoAdminValidationTest(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

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
