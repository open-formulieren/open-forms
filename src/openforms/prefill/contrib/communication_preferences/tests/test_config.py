from django.test import TestCase

from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.customer_interactions.tests.factories import (
    CustomerInteractionsAPIGroupConfigFactory,
)
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.utils.tests.vcr import OFVCRMixin

from ..plugin import ProfileCommunicationPreferences


class CommunicationPreferencesConfigTests(OFVCRMixin, TestCase):
    def test_config_invalid(self):
        plugin = ProfileCommunicationPreferences("communication_preferences-invalid")
        invalid_service = ServiceFactory.create(
            api_root="http://localhost:8005/klantinteracties/api/v1/invalid/",
            api_type=APITypes.kc,
            header_key="Authorization",
            header_value="Token INVALID",
            auth_type=AuthTypes.api_key,
        )
        CustomerInteractionsAPIGroupConfigFactory.create(
            customer_interactions_service=invalid_service
        )

        with self.assertRaises(InvalidPluginConfiguration):
            plugin.check_config()
