from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.authentication.contrib.digid_eherkenning_oidc.models import (
    OpenIDConnectPublicConfig,
)
from openforms.config.models import GlobalConfiguration
from openforms.forms.models import Form
from openforms.forms.tests.factories import FormFactory

default_config = dict(
    enabled=True,
    oidc_rp_client_id="testclient",
    oidc_rp_client_secret="secret",
    oidc_rp_sign_algo="RS256",
    oidc_rp_scopes_list=["openid", "bsn"],
    oidc_op_jwks_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/certs",
    oidc_op_authorization_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/auth",
    oidc_op_token_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/token",
    oidc_op_user_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
    oidc_op_logout_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/logout",
)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class DigiDOIDCFormAdminTests(WebTest):
    def setUp(self):
        super().setUp()

        self.user = SuperUserFactory.create(app=self.app)
        self.app.set_user(self.user)

        global_config = GlobalConfiguration.get_solo()
        global_config.enable_react_form = False
        global_config.save()

        def _cleanup():
            GlobalConfiguration.get_solo().delete()

        self.addCleanup(_cleanup)

    @patch(
        "openforms.authentication.contrib.digid_eherkenning_oidc.models.OpenIDConnectPublicConfig.get_solo",
        return_value=OpenIDConnectPublicConfig(**default_config),
    )
    def test_digid_oidc_enabled(self, *m):
        response = self.app.get(reverse("admin:forms_form_add"))

        form = response.form

        form["name"] = "testform"
        form["slug"] = "testform"
        form["authentication_backends"] = "digid_oidc"

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        self.assertTrue(Form.objects.exists())

        form = Form.objects.get()
        self.assertEqual(form.authentication_backends, ["digid_oidc"])

    @patch(
        "openforms.authentication.contrib.digid_eherkenning_oidc.models.OpenIDConnectPublicConfig.get_solo",
        return_value=OpenIDConnectPublicConfig(**default_config),
    )
    @patch(
        "openforms.plugins.registry.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            plugin_configuration={
                "authentication": {
                    "digid_oidc": {"enabled": False},
                },
            },
            enable_react_form=False,
        ),
    )
    def test_digid_oidc_not_enabled(self, *m):
        response = self.app.get(reverse("admin:forms_form_add"))

        form = response.form

        form["name"] = "testform"
        form["slug"] = "testform"
        form["authentication_backends"] = "digid_oidc"

        response = form.submit()

        self.assertEqual(response.status_code, 200)

        self.assertFalse(Form.objects.exists())

    def test_digid_oidc_disable_allowed(self):
        # Patching `get_solo()` doesn't seem to work when retrieving the change_form
        config = OpenIDConnectPublicConfig(**default_config)
        config.save()

        FormFactory.create(authentication_backends=["eherkenning_oidc"])

        response = self.app.get(
            reverse("admin:digid_eherkenning_oidc_openidconnectpublicconfig_change")
        )

        form = response.form
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(OpenIDConnectPublicConfig.get_solo().enabled)

    def test_digid_oidc_disable_not_allowed(self):
        # Patching `get_solo()` doesn't seem to work when retrieving the change_form
        config = OpenIDConnectPublicConfig(**default_config)
        config.save()

        FormFactory.create(authentication_backends=["digid_oidc"])

        response = self.app.get(
            reverse("admin:digid_eherkenning_oidc_openidconnectpublicconfig_change")
        )

        form = response.form
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(OpenIDConnectPublicConfig.get_solo().enabled)
