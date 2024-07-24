from unittest import TestCase

from .assertions import FormioMixin

FORMIO_CONFIGURATION = {
    "components": [
        {
            "type": "textfield",
            "key": "text1",
            "defaultValue": "foo",
            "nested": {
                "property": "value",
            },
        }
    ]
}


class FormioMixinAssertionsTests(FormioMixin, TestCase):
    def test_correct_config_subset_properties(self):
        try:
            self.assertFormioComponent(
                FORMIO_CONFIGURATION,
                "text1",
                {
                    "type": "textfield",
                    "defaultValue": "foo",
                },
            )
        except AssertionError:
            self.fail("Assertion should have passed.")

    def test_nested_lookup(self):
        try:
            self.assertFormioComponent(
                FORMIO_CONFIGURATION,
                "text1",
                {
                    "nested.property": "value",
                },
            )
        except AssertionError:
            self.fail("Assertion should have passed.")

    def test_invalid_component_key(self):
        with self.assertRaises(AssertionError):
            self.assertFormioComponent(FORMIO_CONFIGURATION, "bad-key", {})

    def test_component_missing_property(self):
        self._outcome.expecting_failure = True

        self.assertFormioComponent(
            FORMIO_CONFIGURATION, "text1", {"missingProperty": "bar"}
        )

        # Resetting `expecting_failure` to not have the above
        # assertion silently ignored:
        self._outcome.expecting_failure = False
        self.assertIsNotNone(self._outcome.expectedFailure)

    def test_component_unexpected_value(self):
        self._outcome.expecting_failure = True

        self.assertFormioComponent(
            FORMIO_CONFIGURATION, "text1", {"defaultValue": "bar"}
        )

        # Resetting `expecting_failure` to not have the above
        # assertion silently ignored:
        self._outcome.expecting_failure = False
        self.assertIsNotNone(self._outcome.expectedFailure)
