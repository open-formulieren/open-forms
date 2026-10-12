from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from ..plugin import EHerkenningAuthentication


class EHerkenningVendorHintTests(SimpleTestCase):
    @patch("digid_eherkenning.models.EherkenningConfiguration.get_solo")
    def test_get_vendor_hint_uses_metadata_source(self, get_solo):
        get_solo.return_value = MagicMock(
            metadata_file_source="https://idp.example.com/metadata"
        )

        plugin = EHerkenningAuthentication("eherkenning")

        self.assertEqual(plugin.get_vendor_hint({}), "https://idp.example.com/metadata")
