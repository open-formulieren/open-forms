import json

from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from digid_eherkenning_oidc_generics.models import OpenIDConnectEHerkenningConfig
from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.tests.factories import FormFactory

default_config = dict(
    enabled=True,
    oidc_rp_client_id="testclient",
    oidc_rp_client_secret="secret",
    oidc_rp_sign_algo="RS256",
    oidc_rp_scopes_list=["openid", "kvk"],
    oidc_op_jwks_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/certs",
    oidc_op_authorization_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/auth",
    oidc_op_token_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/token",
    oidc_op_user_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
    oidc_op_logout_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/logout",
)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class eHerkenningOIDCFormAdminTests(WebTest):
    def setUp(self):
        super().setUp()

        self.user = SuperUserFactory.create()
        self.app.set_user(self.user)

    def test_eherkenning_oidc_disable_allowed(self):
        # Patching `get_solo()` doesn't seem to work when retrieving the change_form
        config = OpenIDConnectEHerkenningConfig(**default_config)
        config.save()

        FormFactory.create(authentication_backends=["digid_oidc"])

        response = self.app.get(
            reverse(
                "admin:digid_eherkenning_oidc_generics_openidconnecteherkenningconfig_change"
            )
        )

        form = response.form
        form["enabled"] = False
        # set the value manually, normally this is done through JS
        form["oidc_rp_scopes_list"] = json.dumps(config.oidc_rp_scopes_list)
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(OpenIDConnectEHerkenningConfig.get_solo().enabled)

    def test_eherkenning_oidc_disable_not_allowed(self):
        # Patching `get_solo()` doesn't seem to work when retrieving the change_form
        config = OpenIDConnectEHerkenningConfig(**default_config)
        config.save()

        FormFactory.create(authentication_backends=["eherkenning_oidc"])

        response = self.app.get(
            reverse(
                "admin:digid_eherkenning_oidc_generics_openidconnecteherkenningconfig_change"
            )
        )

        form = response.form
        form["enabled"] = False
        # set the value manually, normally this is done through JS
        form["oidc_rp_scopes_list"] = json.dumps(config.oidc_rp_scopes_list)
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(OpenIDConnectEHerkenningConfig.get_solo().enabled)
