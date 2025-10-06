from pathlib import Path
from unittest.mock import patch

from openforms.submissions.tests.factories import SubmissionFactory
from suwinet.tests.factories import SuwinetConfigFactory
from suwinet.tests.test_client import SuwinetTestCase

from ....exceptions import PrefillSkipped
from ..plugin import IdentifierRoles, SuwinetPrefill

DATA_DIR = Path(__file__).parent / "data"


class SuwinetPrefillTests(SuwinetTestCase):
    VCR_TEST_FILES = DATA_DIR

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.config = SuwinetConfigFactory.create(all_endpoints=True)

    def setUp(self):
        super().setUp()
        solo_patcher = patch(
            "suwinet.client.SuwinetConfig.get_solo", return_value=self.config
        )
        solo_patcher.start()
        self.addCleanup(solo_patcher.stop)

    def test_unconfigured_service_gets_no_attributes(self):
        self.config.service = None

        plugin = SuwinetPrefill(identifier="suwinet")

        self.assertEqual(plugin.get_available_attributes(), [])

    def test_get_attributes(self):
        plugin = SuwinetPrefill(identifier="suwinet")

        attributes = sorted(plugin.get_available_attributes())

        # operations with other parameters than just bsn are commented out
        expected = [
            (
                "BRPDossierPersoonGSD.AanvraagPersoon",
                "BRPDossierPersoonGSD > AanvraagPersoon",
            ),
            (
                "Bijstandsregelingen.BijstandsregelingenInfo",
                "Bijstandsregelingen > BijstandsregelingenInfo",
            ),
            (
                "DUODossierPersoonGSD.DUOPersoonsInfo",
                "DUODossierPersoonGSD > DUOPersoonsInfo",
            ),
            (
                "DUODossierStudiefinancieringGSD.DUOStudiefinancieringInfo",
                "DUODossierStudiefinancieringGSD > DUOStudiefinancieringInfo",
            ),
            (
                "GSDDossierReintegratie.GSDReintegratieInfo",
                "GSDDossierReintegratie > GSDReintegratieInfo",
            ),
            # ("IBVerwijsindex.IBVerwijsindex", "IBVerwijsindex > IBVerwijsindex"),
            # (
            #     "KadasterDossierGSD.ObjectInfoKadastraleAanduiding",
            #     "KadasterDossierGSD > ObjectInfoKadastraleAanduiding",
            # ),
            # (
            #     "KadasterDossierGSD.ObjectInfoLocatieOZ",
            #     "KadasterDossierGSD > ObjectInfoLocatieOZ",
            # ),
            (
                "KadasterDossierGSD.PersoonsInfo",
                "KadasterDossierGSD > PersoonsInfo",
            ),
            # (
            #     "RDWDossierDigitaleDiensten.KentekenInfo",
            #     "RDWDossierDigitaleDiensten > KentekenInfo",
            # ),
            (
                "RDWDossierDigitaleDiensten.VoertuigbezitInfoPersoon",
                "RDWDossierDigitaleDiensten > VoertuigbezitInfoPersoon",
            ),
            # ("RDWDossierGSD.KentekenInfo", "RDWDossierGSD > KentekenInfo"),
            # (
            #     "RDWDossierGSD.VoertuigbezitInfoOrg",
            #     "RDWDossierGSD > VoertuigbezitInfoOrg",
            # ),
            # (
            #     "RDWDossierGSD.VoertuigbezitInfoPersoon",
            #     "RDWDossierGSD > VoertuigbezitInfoPersoon",
            # ),
            (
                "SVBDossierPersoonGSD.SVBPersoonsInfo",
                "SVBDossierPersoonGSD > SVBPersoonsInfo",
            ),
            (
                "UWVDossierAanvraagUitkeringStatusGSD.UWVAanvraagUitkeringStatusInfo",
                "UWVDossierAanvraagUitkeringStatusGSD > UWVAanvraagUitkeringStatusInfo",
            ),
            # (
            #     "UWVDossierInkomstenGSD.UWVPersoonsIkvInfo",
            #     "UWVDossierInkomstenGSD > UWVPersoonsIkvInfo",
            # ),
            # (
            #     "UWVDossierInkomstenGSDDigitaleDiensten.UWVPersoonsIkvInfo",
            #     "UWVDossierInkomstenGSDDigitaleDiensten > UWVPersoonsIkvInfo",
            # ),
            (
                "UWVDossierQuotumArbeidsbeperktenGSD.UWVPersoonsArbeidsbeperktenInfo",
                "UWVDossierQuotumArbeidsbeperktenGSD > UWVPersoonsArbeidsbeperktenInfo",
            ),
            (
                "UWVDossierWerknemersverzekeringenGSD.UWVPersoonsWvInfo",
                "UWVDossierWerknemersverzekeringenGSD > UWVPersoonsWvInfo",
            ),
            (
                "UWVDossierWerknemersverzekeringenGSDDigitaleDiensten.UWVPersoonsWvInfo",
                "UWVDossierWerknemersverzekeringenGSDDigitaleDiensten > UWVPersoonsWvInfo",
            ),
            (
                "UWVWbDossierPersoonGSD.UwvWbPersoonsInfo",
                "UWVWbDossierPersoonGSD > UwvWbPersoonsInfo",
            ),
        ]
        self.assertEqual(attributes, expected)

    def test_get_identifier_value(self):
        plugin = SuwinetPrefill(identifier="suwinet")
        submission = SubmissionFactory.create(
            auth_info__value="444444440",
        )
        bsn = plugin.get_identifier_value(submission, IdentifierRoles.main)

        self.assertEqual(bsn, "444444440")

    def test_get_kadaster_values(self):
        plugin = SuwinetPrefill(identifier="suwinet")
        submission = SubmissionFactory.create(auth_info__value="444444440")

        values = plugin.get_prefill_values(
            submission, ["KadasterDossierGSD.PersoonsInfo"]
        )
        self.assertTrue(
            values
        )  # contents is already asserted in the Suwinet client tests

    def test_unconfigured_service_gets_no_prefill_values(self):
        self.config.service = None

        plugin = SuwinetPrefill(identifier="suwinet")
        submission = SubmissionFactory.create(auth_info__value="444444440")

        values = plugin.get_prefill_values(
            submission, ["KadasterDossierGSD.PersoonsInfo"]
        )
        self.assertEqual(values, {})

    def test_unauthenticated_filler_gets_no_prefill_values(self):
        plugin = SuwinetPrefill(identifier="suwinet")
        submission = SubmissionFactory.create()

        with self.assertRaises(PrefillSkipped):
            plugin.get_prefill_values(submission, ["KadasterDossierGSD.PersoonsInfo"])

    def test_failed_respones(self):
        # My close friend, good ol' Policy Falsified
        plugin = SuwinetPrefill(identifier="suwinet")
        submission = SubmissionFactory.create(auth_info__value="444444440")

        values = plugin.get_prefill_values(
            submission, ["UWVWbDossierPersoonGSD.UwvWbPersoonsInfo"]
        )

        # still returns empty values
        self.assertEqual(values, {})
