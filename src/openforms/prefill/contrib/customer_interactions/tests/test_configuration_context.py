from django.test import TestCase

from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.customer_interactions.tests.factories import (
    CustomerInteractionsAPIGroupConfigFactory,
)

from ..plugin import CommunicationPreferences


class CommunicationPreferencesConfigTests(TestCase):
    def test_configuration_context(self):
        plugin = CommunicationPreferences
        service1, service2 = ServiceFactory.create_batch(2)
        CustomerInteractionsAPIGroupConfigFactory.create(
            customer_interactions_service=service1, name="Group 1", identifier="group-1"
        )
        CustomerInteractionsAPIGroupConfigFactory.create(
            customer_interactions_service=service2, name="Group 2", identifier="group-2"
        )

        self.assertEqual(
            plugin.configuration_context(),
            {"api_groups": [["group-1", "Group 1"], ["group-2", "Group 2"]]},
        )
