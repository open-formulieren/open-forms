from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from ..plugin import DigidAuthentication


class DigidAuthenticationVendorHintTests(SimpleTestCase):
    def setUp(self):
        self.plugin = DigidAuthentication("digid")

    @patch("digid_eherkenning.models.DigidConfiguration.get_solo")
    def test_get_vendor_hint_success(self, mock_get_solo):
        mock_get_solo.return_value = MagicMock(
            metadata_file_source="https://idp.example.com/metadata"
        )

        self.assertEqual(
            self.plugin.get_vendor_hint({}), "https://idp.example.com/metadata"
        )

    @patch("digid_eherkenning.models.DigidConfiguration.get_solo")
    def test_get_vendor_hint_without_source(self, mock_get_solo):
        mock_get_solo.return_value = MagicMock(metadata_file_source="")

        self.assertIsNone(self.plugin.get_vendor_hint({}))
