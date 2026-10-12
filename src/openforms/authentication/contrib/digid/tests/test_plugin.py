from unittest.mock import patch

from django.test import SimpleTestCase

from digid_eherkenning.models import DigidConfiguration

from ..plugin import DigidAuthentication


class DigidAuthenticationVendorHintTests(SimpleTestCase):
    def setUp(self):
        self.plugin = DigidAuthentication("digid")

    def _get_options(self):
        assert self.plugin.configuration_options is not None
        serializer = self.plugin.configuration_options(data={})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    @patch("digid_eherkenning.models.DigidConfiguration.get_solo")
    def test_get_vendor_hint_success(self, mock_get_solo):
        mock_get_solo.return_value = DigidConfiguration(
            metadata_file_source="https://idp.example.com/metadata"
        )

        self.assertEqual(
            self.plugin.get_vendor_hint(self._get_options()),
            "https://idp.example.com/metadata",
        )

    @patch("digid_eherkenning.models.DigidConfiguration.get_solo")
    def test_get_vendor_hint_without_source(self, mock_get_solo):
        mock_get_solo.return_value = DigidConfiguration(metadata_file_source="")

        self.assertIsNone(self.plugin.get_vendor_hint(self._get_options()))
