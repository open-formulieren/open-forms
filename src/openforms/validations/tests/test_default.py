from unittest.mock import patch

from django.test import TestCase

from openforms.config.models import GlobalConfiguration
from openforms.validations.registry import register


class DefaultRegistryTest(TestCase):
    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_registered_validators(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(
            enable_demo_plugins=False,
        )
        expected_identifiers = {
            "kvk-kvkNumber",
            "kvk-branchNumber",
            "kvk-rsin",
            "phonenumber-international",
            "phonenumber-nl",
        }
        have = set(r.identifier for r in register.iter_enabled_plugins())

        # check if all expected/required validators are registered
        self.assertEqual(have, set(expected_identifiers))
