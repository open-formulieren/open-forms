from django.test import TestCase

from openforms.utils.tests.feature_flags import enable_feature_flag
from openforms.validations.registry import register


class DefaultRegistryTest(TestCase):
    @enable_feature_flag("ENABLE_DEMO_PLUGINS")
    def test_registered_validators(self):
        expected_identifiers = {
            "brk-zakelijk-gerechtigd",
            "kvk-kvkNumber",
            "kvk-branchNumber",
            "kvk-rsin",
            "phonenumber-international",
            "phonenumber-nl",
        }
        have = set(r.identifier for r in register.iter_enabled_plugins())

        # check if all expected/required validators are registered
        self.assertEqual(have, set(expected_identifiers))
