from pathlib import Path
from unittest import expectedFailure
from unittest.mock import patch

from openforms.forms.tests.factories import FormVariableDataTypes, FormVariableFactory
from openforms.prefill import prefill_variables
from openforms.submissions.tests.factories import SubmissionFactory
from suwinet.tests.factories import SuwinetConfigFactory
from suwinet.tests.test_client import SuwinetTestCase

from ....registry import Registry
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

    def test_binding_to_variable(self):
        register = Registry()
        register("suwinet")(SuwinetPrefill)
        form_var = FormVariableFactory.create(
            form__generate_minimal_setup=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin="suwinet",
            prefill_attribute="KadasterDossierGSD.PersoonsInfo",
        )
        submission = SubmissionFactory.create(
            form=form_var.form,
            auth_info__value="444444440",
        )

        prefill_variables(submission, register)
        var = submission.submissionvaluevariable_set.get()

        self.assertTrue(
            var.value
        )  # contents is already asserted in the Suwinet client tests

    @expectedFailure
    def test_collect_gateway_mock_failures(self):
        # As we speak we only know how to get mock data from the KadasterDossierGSD
        # this test collects a VHS cassette with (Den Haag) Layer 7 Gateway failures
        # and empty endpoint responses. These bsns are bsns that have been reported
        # to return mock data.
        #
        # So the cassette does not represent "correct" responses, but just gives
        # insight into what operations we haven't seen working, either because
        # we don't get through the gateway, or we don't know a bsn for the operation
        # that returns mock data.
        #
        # this "try what could work and see what sticks" test should be replaced with
        # a mapping like {"Service.Operation": "bsn"}, and just try one, known good mock
        # operation and check it returns a dict.

        plugin = SuwinetPrefill(identifier="suwinet")
        # What can I get for 5 dollars?
        everything = [a for a, label in plugin.get_available_attributes()]

        bsns = [
            "111111110",
            "444444440",
            "112233454",
            "999996769",
        ]
        for submission in (
            SubmissionFactory.create(auth_info__value=bsn) for bsn in bsns
        ):
            with self.subTest(f"Get ALL the things for {submission.auth_info}"):
                values = plugin.get_prefill_values(submission, everything)
                self.assertTrue(values)
