from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.config.models import GlobalConfiguration
from openforms.forms.models import Form
from openforms.forms.tests.factories import FormFactory

from ..models import OpenIDConnectEHerkenningConfig


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class eHerkenningOIDCFormAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = OpenIDConnectEHerkenningConfig.get_solo()
        config.enabled = True
        config.oidc_rp_client_id = "testclient"
        config.oidc_rp_client_secret = "secret"
        config.oidc_rp_sign_algo = "RS256"
        config.oidc_rp_scopes_list = ["openid", "kvk"]

        config.oidc_op_jwks_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/certs"
        )
        config.oidc_op_authorization_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth"
        )
        config.oidc_op_token_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/token"
        )
        config.oidc_op_user_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/userinfo"
        )
        config.oidc_op_logout_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/logout"
        )
        config.save()

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

    def test_eherkenning_oidc_enabled(self):
        response = self.app.get(reverse("admin:forms_form_add"))

        form = response.form

        form["name"] = "testform"
        form["slug"] = "testform"
        form["authentication_backends"] = "eherkenning_oidc"

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        self.assertTrue(Form.objects.exists())

        form = Form.objects.get()
        self.assertEqual(form.authentication_backends, ["eherkenning_oidc"])

    def test_eherkenning_oidc_not_enabled(self):
        config = OpenIDConnectEHerkenningConfig.get_solo()
        config.enabled = False
        config.save()

        response = self.app.get(reverse("admin:forms_form_add"))

        form = response.form

        form["name"] = "testform"
        form["slug"] = "testform"
        form["authentication_backends"] = "eherkenning_oidc"

        response = form.submit()

        self.assertEqual(response.status_code, 200)

        self.assertFalse(Form.objects.exists())

    def test_eherkenning_oidc_disable_allowed(self):
        config = OpenIDConnectEHerkenningConfig.get_solo()
        config.enabled = True
        config.save()

        FormFactory.create(authentication_backends=["digid_oidc"])

        response = self.app.get(
            reverse("admin:eherkenning_oidc_openidconnecteherkenningconfig_change")
        )

        form = response.form
        form["enabled"] = False
        response = form.submit()
        self.assertEqual(response.status_code, 302)

        config.refresh_from_db()
        self.assertFalse(config.enabled)

    def test_eherkenning_oidc_disable_not_allowed(self):
        config = OpenIDConnectEHerkenningConfig.get_solo()
        config.enabled = True
        config.save()

        FormFactory.create(authentication_backends=["eherkenning_oidc"])

        response = self.app.get(
            reverse("admin:eherkenning_oidc_openidconnecteherkenningconfig_change")
        )

        form = response.form
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)

        config.refresh_from_db()
        self.assertTrue(config.enabled)
