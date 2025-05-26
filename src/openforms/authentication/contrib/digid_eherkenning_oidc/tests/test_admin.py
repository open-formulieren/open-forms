import json

from django.contrib.postgres.fields import ArrayField
from django.test import override_settings
from django.urls import reverse_lazy

from digid_eherkenning.oidc.models import BaseConfig
from django_jsonform.models.fields import JSONField
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.tests.factories import FormFactory

from ..models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
    OFEIDASConfig,
)


# disable django solo cache to prevent test isolation breakage
@override_settings(SOLO_CACHE=None)
@disable_admin_mfa()
class AdminTestsBase(WebTest):
    pass


def _set_arrayfields(form, config: BaseConfig) -> None:
    """
    Set the field values manually, normally this is done through JS in the admin.
    """
    fields = [
        f.name
        for f in config._meta.get_fields()
        if isinstance(f, ArrayField | JSONField)
    ]
    for field in fields:
        form[field] = json.dumps(getattr(config, field))


class DigiDConfigAdminTests(AdminTestsBase):
    CHANGE_PAGE_URL = reverse_lazy("admin:digid_eherkenning_oidc_ofdigidconfig_change")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # minimal configuration to pass form validation & not do network IO
        cls.config = config = OFDigiDConfig(
            enabled=True,
            oidc_rp_client_id="testclient",
            oidc_rp_client_secret="secret",
            oidc_op_authorization_endpoint="http://localhost/oidc/auth",
            oidc_op_token_endpoint="http://localhost/oidc/token",
            oidc_op_user_endpoint="http://localhost/oidc/userinfo",
            oidc_op_logout_endpoint="http://localhost/oidc/logout",
        )
        config.save()
        cls.user = SuperUserFactory.create()

    def test_can_disable_backend_iff_unused_in_forms(self):
        FormFactory.create(authentication_backend="other-backend")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofdigidconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.config.refresh_from_db()
        self.assertFalse(self.config.enabled)

    def test_cannot_disable_backend_if_used_in_any_form(self):
        FormFactory.create(authentication_backend="digid_oidc")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofdigidconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)  # there are validation errors
        self.config.refresh_from_db()
        self.assertTrue(self.config.enabled)

    def test_leave_enabled(self):
        FormFactory.create(authentication_backend="other-backend")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofdigidconfig_form"]
        _set_arrayfields(form, self.config)

        # enable the backend
        form["enabled"] = True
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.config.refresh_from_db()
        self.assertTrue(self.config.enabled)


class DigiDMachtigenConfigAdminTests(AdminTestsBase):
    CHANGE_PAGE_URL = reverse_lazy(
        "admin:digid_eherkenning_oidc_ofdigidmachtigenconfig_change"
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # minimal configuration to pass form validation & not do network IO
        cls.config = config = OFDigiDMachtigenConfig(
            enabled=True,
            oidc_rp_client_id="testclient",
            oidc_rp_client_secret="secret",
            oidc_op_authorization_endpoint="http://localhost/oidc/auth",
            oidc_op_token_endpoint="http://localhost/oidc/token",
            oidc_op_user_endpoint="http://localhost/oidc/userinfo",
            oidc_op_logout_endpoint="http://localhost/oidc/logout",
        )
        config.save()
        cls.user = SuperUserFactory.create()

    def test_can_disable_backend_iff_unused_in_forms(self):
        FormFactory.create(authentication_backend="other-backend")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofdigidmachtigenconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.config.refresh_from_db()
        self.assertFalse(self.config.enabled)

    def test_cannot_disable_backend_if_used_in_any_form(self):
        FormFactory.create(authentication_backend="digid_machtigen_oidc")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofdigidmachtigenconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)  # there are validation errors
        self.config.refresh_from_db()
        self.assertTrue(self.config.enabled)


class EHerkenningConfigAdminTests(AdminTestsBase):
    CHANGE_PAGE_URL = reverse_lazy(
        "admin:digid_eherkenning_oidc_ofeherkenningconfig_change"
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # minimal configuration to pass form validation & not do network IO
        cls.config = config = OFEHerkenningConfig(
            enabled=True,
            oidc_rp_client_id="testclient",
            oidc_rp_client_secret="secret",
            oidc_op_authorization_endpoint="http://localhost/oidc/auth",
            oidc_op_token_endpoint="http://localhost/oidc/token",
            oidc_op_user_endpoint="http://localhost/oidc/userinfo",
            oidc_op_logout_endpoint="http://localhost/oidc/logout",
        )
        config.save()
        cls.user = SuperUserFactory.create()

    def test_can_disable_backend_iff_unused_in_forms(self):
        FormFactory.create(authentication_backend="other-backend")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofeherkenningconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.config.refresh_from_db()
        self.assertFalse(self.config.enabled)

    def test_cannot_disable_backend_if_used_in_any_form(self):
        FormFactory.create(authentication_backend="eherkenning_oidc")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofeherkenningconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)  # there are validation errors
        self.config.refresh_from_db()
        self.assertTrue(self.config.enabled)


class EHerkenningBewindvoeringConfigAdminTests(AdminTestsBase):
    CHANGE_PAGE_URL = reverse_lazy(
        "admin:digid_eherkenning_oidc_ofeherkenningbewindvoeringconfig_change"
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # minimal configuration to pass form validation & not do network IO
        cls.config = config = OFEHerkenningBewindvoeringConfig(
            enabled=True,
            oidc_rp_client_id="testclient",
            oidc_rp_client_secret="secret",
            oidc_op_authorization_endpoint="http://localhost/oidc/auth",
            oidc_op_token_endpoint="http://localhost/oidc/token",
            oidc_op_user_endpoint="http://localhost/oidc/userinfo",
            oidc_op_logout_endpoint="http://localhost/oidc/logout",
        )
        config.save()
        cls.user = SuperUserFactory.create()

    def test_can_disable_backend_iff_unused_in_forms(self):
        FormFactory.create(authentication_backend="other-backend")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofeherkenningbewindvoeringconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.config.refresh_from_db()
        self.assertFalse(self.config.enabled)

    def test_cannot_disable_backend_if_used_in_any_form(self):
        FormFactory.create(authentication_backend="eherkenning_bewindvoering_oidc")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofeherkenningbewindvoeringconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)  # there are validation errors
        self.config.refresh_from_db()
        self.assertTrue(self.config.enabled)


class EIDASConfigAdminTests(AdminTestsBase):
    CHANGE_PAGE_URL = reverse_lazy("admin:digid_eherkenning_oidc_ofeidasconfig_change")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # minimal configuration to pass form validation & not do network IO
        cls.config = config = OFEIDASConfig(
            enabled=True,
            oidc_rp_client_id="testclient",
            oidc_rp_client_secret="secret",
            oidc_op_authorization_endpoint="http://localhost/oidc/auth",
            oidc_op_token_endpoint="http://localhost/oidc/token",
            oidc_op_user_endpoint="http://localhost/oidc/userinfo",
            oidc_op_logout_endpoint="http://localhost/oidc/logout",
        )
        config.save()
        cls.user = SuperUserFactory.create()

    def test_can_disable_backend_iff_unused_in_forms(self):
        FormFactory.create(authentication_backend="other-backend")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofeidasconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.config.refresh_from_db()
        self.assertFalse(self.config.enabled)

    def test_cannot_disable_backend_if_used_in_any_form(self):
        FormFactory.create(authentication_backend="eidas_oidc")
        change_page = self.app.get(self.CHANGE_PAGE_URL, user=self.user)

        form = change_page.forms["ofeidasconfig_form"]
        _set_arrayfields(form, self.config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)  # there are validation errors
        self.config.refresh_from_db()
        self.assertTrue(self.config.enabled)
