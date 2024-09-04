from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from digid_eherkenning.models import DigidConfiguration

from ..tasks import update_saml_metadata

BASE_DIR = Path(__file__).parent.resolve()
DIGID_TEST_METADATA_FILE_SLO_POST = (
    BASE_DIR / "files" / "digid" / "metadata_with_slo_POST"
)
EHERKENNING_TEST_METADATA_FILE = BASE_DIR / "files" / "eherkenning" / "metadata"


class UpdateSamlTaskTests(TestCase):
    @patch(
        "onelogin.saml2.idp_metadata_parser.OneLogin_Saml2_IdPMetadataParser.get_metadata"
    )
    def test_command_for_digid_update_is_executed(self, get_metadata):
        config = DigidConfiguration.get_solo()

        with DIGID_TEST_METADATA_FILE_SLO_POST.open("rb") as metadata_file:
            metadata_content = metadata_file.read().decode("utf-8")
            get_metadata.return_value = metadata_content
            config.metadata_file_source = (
                "https://was-preprod1.digid.nl/saml/idp/metadata"
            )
            config.save()

            self.assertEqual(get_metadata.call_count, 1)

            get_metadata.reset_mock()

        update_saml_metadata()

        self.assertEqual(get_metadata.call_count, 1)

    @patch(
        "onelogin.saml2.idp_metadata_parser.OneLogin_Saml2_IdPMetadataParser.get_metadata"
    )
    def test_command_for_eherkenning_update_is_executed(self, get_metadata):
        config = DigidConfiguration.get_solo()

        with EHERKENNING_TEST_METADATA_FILE.open("rb") as metadata_file:
            metadata_content = metadata_file.read().decode("utf-8")
            get_metadata.return_value = metadata_content
            config.metadata_file_source = (
                "https://eh01.staging.iwelcome.nl/broker/sso/1.13"
            )
            config.save()

            self.assertEqual(get_metadata.call_count, 1)

            get_metadata.reset_mock()

        update_saml_metadata()

        self.assertEqual(get_metadata.call_count, 1)
