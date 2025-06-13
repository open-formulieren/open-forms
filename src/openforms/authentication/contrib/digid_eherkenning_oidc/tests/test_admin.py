import json

from django.contrib.postgres.fields import ArrayField
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext

from django_jsonform.models.fields import JSONField
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from mozilla_django_oidc_db.models import OIDCClient
from mozilla_django_oidc_db.tests.factories import (
    OIDCProviderFactory,
)

from oidc_plugins.constants import OIDC_DIGID_IDENTIFIER
from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.tests.factories import FormFactory


# disable django solo cache to prevent test isolation breakage
@override_settings(SOLO_CACHE=None)
@disable_admin_mfa()
class AdminTestsBase(WebTest):
    pass


def _set_arrayfields(form, config: OIDCClient) -> None:
    """
    Set the field values manually, normally this is done through JS in the admin.
    """
    fields = [
        f.name
        for f in config._meta.get_fields()
        if isinstance(f, (ArrayField, JSONField))
    ]
    for field in fields:
        form[field] = json.dumps(getattr(config, field))


class DigiDConfigAdminTests(AdminTestsBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # minimal configuration to pass form validation & not do network IO
        cls.provider = OIDCProviderFactory.create(
            identifier="admin-oidc-provider",
            oidc_op_authorization_endpoint="http://localhost/oidc/auth",
            oidc_op_token_endpoint="http://localhost/oidc/token",
            oidc_op_user_endpoint="http://localhost/oidc/userinfo",
            oidc_op_logout_endpoint="http://localhost/oidc/logout",
        )
        cls.user = SuperUserFactory.create()

    def test_can_disable_backend_iff_unused_in_forms(self):
        FormFactory.create(authentication_backend="other-backend")

        config, _ = OIDCClient.objects.update_or_create(
            identifier="admin-oidc",
            defaults={
                "enabled": True,
                "oidc_rp_client_id": "testclient",
                "oidc_rp_client_secret": "secret",
                "oidc_provider": self.provider,
                "options": {
                    "user_settings": {
                        "claim_mappings": {
                            "username": ["sub"],
                            "first_name": [],
                            "last_name": [],
                            "email": [],
                        },
                        "username_case_sensitive": True,
                        "sensitive_claims": [],
                    },
                    "groups_settings": {
                        "claim_mapping": ["groups"],
                        "sync": True,
                        "sync_pattern": "*",
                        "make_users_staff": False,
                        "superuser_group_names": [],
                        "default_groups": [],
                    },
                },
            },
        )

        change_page = self.app.get(
            reverse(
                "admin:mozilla_django_oidc_db_oidcclient_change",
                kwargs={"object_id": config.pk},
            ),
            user=self.user,
        )

        form = change_page.forms["oidcclient_form"]
        _set_arrayfields(form, config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 302)

        config.refresh_from_db()

        self.assertFalse(config.enabled)

    def test_cannot_disable_backend_if_used_in_any_form(self):
        FormFactory.create(authentication_backend="digid_oidc")

        config, _ = OIDCClient.objects.update_or_create(
            identifier=OIDC_DIGID_IDENTIFIER,
            defaults={
                "enabled": True,
                "oidc_rp_client_id": "testclient",
                "oidc_rp_client_secret": "secret",
                "oidc_provider": self.provider,
                "options": {
                    "loa_settings": {
                        "claim_path": ["loa"],
                        "default": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
                        "value_mapping": [],
                    },
                    "identity_settings": {
                        "bsn_claim_path": ["bsn"],
                    },
                },
            },
        )

        change_page = self.app.get(
            reverse(
                "admin:mozilla_django_oidc_db_oidcclient_change",
                kwargs={"object_id": config.pk},
            ),
            user=self.user,
        )

        form = change_page.forms["oidcclient_form"]
        _set_arrayfields(form, config)

        # disable the backend
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)  # there are validation errors

        expected_error = gettext(
            "{plugin_name} is selected as authentication backend for one or more forms, please remove this backend from these forms before disabling this authentication backend."
        ).format(plugin_name="DigiD via OpenID Connect")
        self.assertIn(expected_error, response.content.decode("UTF-8"))

        config.refresh_from_db()

        self.assertTrue(config.enabled)

    def test_leave_enabled(self):
        FormFactory.create(authentication_backend="other-backend")
        config, _ = OIDCClient.objects.update_or_create(
            identifier=OIDC_DIGID_IDENTIFIER,
            defaults={
                "enabled": True,
                "oidc_rp_client_id": "testclient",
                "oidc_rp_client_secret": "secret",
                "oidc_provider": self.provider,
                "options": {
                    "loa_settings": {
                        "claim_path": ["loa"],
                        "default": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
                        "value_mapping": [],
                    },
                    "identity_settings": {
                        "bsn_claim_path": ["bsn"],
                    },
                },
            },
        )

        change_page = self.app.get(
            reverse(
                "admin:mozilla_django_oidc_db_oidcclient_change",
                kwargs={"object_id": config.pk},
            ),
            user=self.user,
        )

        form = change_page.forms["oidcclient_form"]
        _set_arrayfields(form, config)

        # enable the backend
        form["enabled"] = True
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        config.refresh_from_db()
        self.assertTrue(config.enabled)
