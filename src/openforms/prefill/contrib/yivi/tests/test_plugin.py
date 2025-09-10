from django.test import SimpleTestCase, override_settings

from ..plugin import YiviPrefill


class ConfigurationTests(SimpleTestCase):
    maxDiff = None

    @override_settings(LANGUAGE_CODE="en")
    def test_configuration_context(self):
        configuration_context = YiviPrefill.configuration_context()

        expected = {
            "fixed_attributes": [
                {
                    "attribute": "_internal.auth_info.value",
                    "label": "Identifier value",
                    "auth_attribute": "",
                },
                {
                    "attribute": "_internal.bsn",
                    "label": "BSN",
                    "auth_attribute": "bsn",
                },
                {
                    "attribute": "_internal.kvk",
                    "label": "KvK number",
                    "auth_attribute": "kvk",
                },
                {
                    "attribute": "_internal.pseudo",
                    "label": "Pseudo ID",
                    "auth_attribute": "pseudo",
                },
            ],
        }
        self.assertEqual(configuration_context, expected)
