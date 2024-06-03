from unittest.mock import patch

from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.config.models import GlobalConfiguration

from ..models import PrefillConfig


class PrefillConfigTests(WebTest):
    def test_repr(self):
        instance = PrefillConfig()

        self.assertEqual(str(instance), PrefillConfig._meta.verbose_name)

    @disable_admin_mfa()
    @patch(
        "openforms.plugins.plugin.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            plugin_configuration={
                "registration": {
                    "stufbg": {"enabled": True},
                    "haalcentraal": {"enabled": True},
                    "kvk-kvknumber": {"enabled": True},
                },
            }
        ),
    )
    def test_registry_list_for_defaults(self, m_global_config):
        user = SuperUserFactory.create()
        (
            config,
            _,
        ) = (
            PrefillConfig.objects.get_or_create()
        )  # not using get_solo for cache reasons
        url = reverse("admin:prefill_prefillconfig_change", args=(config.pk,))

        response = self.app.get(url, user=user)

        # check that it's a dropdown-like widget with options/choices
        form = response.forms["prefillconfig_form"]
        self.assertGreater(len(form["default_person_plugin"].options), 1)
        self.assertGreater(len(form["default_company_plugin"].options), 1)
