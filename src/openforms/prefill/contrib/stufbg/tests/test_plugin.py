from unittest.mock import patch

from django.test import TestCase, tag

from openforms.prefill.constants import IdentifierRoles
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory
from stuf.stuf_bg.checks import is_empty_wrapped_response, is_object_not_found_response
from stuf.stuf_bg.constants import FieldChoices
from stuf.stuf_bg.models import StufBGConfig
from stuf.stuf_bg.tests.mixins import StUFBGAssertionsMixin
from stuf.tests.factories import StufServiceFactory

from ....exceptions import PrefillSkipped
from ..plugin import StufBgPrefill


class StufBgPrefillTests(StUFBGAssertionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.stuf_bg_service = StufServiceFactory.create()
        cls.submission: Submission = SubmissionFactory.create(
            auth_info__value="999992314"
        )

    def setUp(self) -> None:
        super().setUp()

        self.plugin = StufBgPrefill("test-plugin")

        # mock out django-solo interface (we don't have to deal with caches then)
        stufbg_config_patcher = patch(
            "openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo",
            return_value=StufBGConfig(service=self.stuf_bg_service),
        )
        stufbg_config_patcher.start()
        self.addCleanup(stufbg_config_patcher.stop)

    def test_getting_available_attributes(self):
        attributes = self.plugin.get_available_attributes()
        self.assertIsInstance(attributes, list)

        for entry in attributes:
            with self.subTest(entry=entry):
                self.assertIsInstance(entry, tuple)
                self.assertEqual(len(entry), 2)
                value, label = entry
                self.assertEqual(value, str(value))
                self.assertEqual(label, str(label))

    def test_get_available_attributes_returns_correct_attributes(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgResponse.xml", self.stuf_bg_service
        )

        # validate response
        self.assertSoapBodyIsValid(response_content)

        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]

        values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values["bsn"], "999992314")
        self.assertEqual(values["voornamen"], "Media")
        self.assertEqual(values["voorletters"], "M")
        self.assertEqual(values["geslachtsnaam"], "Maykin")
        self.assertEqual(values["straatnaam"], "Keizersgracht")
        self.assertEqual(values["huisnummer"], "117")
        self.assertEqual(values["huisletter"], "A")
        self.assertEqual(values["huisnummertoevoeging"], "B")
        self.assertEqual(values["postcode"], "1015 CJ")
        self.assertEqual(values["woonplaatsNaam"], "Amsterdam")

    def test_response_external_municipality_returns_correct_attributes(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgResponseGemeenteVanInschrijving.xml",
            self.stuf_bg_service,
        )

        # validate response
        self.assertSoapBodyIsValid(response_content)

        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]

        values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values["bsn"], "999992314")
        self.assertEqual(values["voornamen"], "Media")
        self.assertEqual(values["geslachtsnaam"], "Maykin")
        self.assertEqual(values["straatnaam"], "Keizersgracht")
        self.assertEqual(values["huisnummer"], "117")
        self.assertEqual(values["huisletter"], "A")
        self.assertEqual(values["huisnummertoevoeging"], "B")
        self.assertEqual(values["postcode"], "1015 CJ")
        self.assertEqual(values["gemeenteVanInschrijving"], "0363")

    def test_get_available_attributes_when_some_attributes_are_not_returned(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgResponseMissingSomeData.xml",
            self.stuf_bg_service,
        )

        # validate response
        self.assertSoapBodyIsValid(response_content)

        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]

        values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values["bsn"], "999992314")
        self.assertEqual(values["voornamen"], "Media")
        self.assertEqual(values["geslachtsnaam"], "Maykin")
        self.assertEqual(values["straatnaam"], "Keizersgracht")
        self.assertEqual(values["huisnummer"], "117")
        self.assertEqual(values["postcode"], "1015 CJ")
        self.assertEqual(values["woonplaatsNaam"], "Amsterdam")
        self.assertNotIn("huisnummertoevoeging", values)
        self.assertNotIn("huisletter", values)

    def test_voorvoegsel_is_parsed(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgResponseWithVoorvoegsel.xml",
            self.stuf_bg_service,
        )

        # validate response
        self.assertSoapBodyIsValid(response_content)

        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]

        values = self.plugin.get_prefill_values(self.submission, attributes)

        self.assertEqual(values["bsn"], "999992314")
        self.assertEqual(values["voornamen"], "Media")
        self.assertEqual(values["voorvoegselGeslachtsnaam"], "van")
        self.assertEqual(values["geslachtsnaam"], "Maykin")
        self.assertEqual(values["straatnaam"], "Keizersgracht")
        self.assertEqual(values["huisnummer"], "117")
        self.assertEqual(values["huisletter"], "A")
        self.assertEqual(values["huisnummertoevoeging"], "B")
        self.assertEqual(values["postcode"], "1015 CJ")
        self.assertEqual(values["woonplaatsNaam"], "Amsterdam")

    def test_get_available_attributes_when_error_occurs(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgErrorResponse.xml",
            self.stuf_bg_service,
        )

        # response validation not needed for the fault
        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]

        with self.assertRaises(ValueError):
            self.plugin.get_prefill_values(self.submission, attributes)

    def test_get_available_attributes_when_no_answer_is_returned(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgNoAnswerResponse.xml",
            self.stuf_bg_service,
        )

        # validate response
        self.assertSoapBodyIsValid(response_content)

        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]

        try:
            values = self.plugin.get_prefill_values(self.submission, attributes)
        except ValueError:
            # empty responses should be handled graciously
            self.fail("No fault/error expected.")

        self.assertEqual(values, {})

    def test_get_available_attributes_when_object_not_found_reponse_is_returned(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgNotFoundResponse.xml",
            self.stuf_bg_service,
        )

        # response validation not needed for the fault
        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]

        with self.assertRaises(ValueError):
            self.plugin.get_prefill_values(self.submission, attributes)

    def test_get_available_attributes_when_empty_reponse_is_returned(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgNoObjectResponse.xml",
            self.stuf_bg_service,
        )

        # validate response
        self.assertSoapBodyIsValid(response_content)

        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]

        try:
            values = self.plugin.get_prefill_values(self.submission, attributes)
        except ValueError:
            # empty responses should be handled graciously
            self.fail("No fault/error expected.")

        self.assertEqual(values, {})

    @tag("gh-1617")
    def test_onvolledige_datum(self):
        """
        Regression test for StUF-onvolledigeDatum responses.

        See issue #1617 on Github.
        """
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgResponseOnvolledigeDatum.xml",
            self.stuf_bg_service,
        )

        # validate response
        self.assertSoapBodyIsValid(response_content)

        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)

        values = self.plugin.get_prefill_values(self.submission, ["geboortedatum"])

        self.assertEqual(values["geboortedatum"], "19600701")

    def test_prefill_values_not_authenticated(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgResponse.xml",
            self.stuf_bg_service,
        )

        # validate response
        self.assertSoapBodyIsValid(response_content)

        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]
        submission = SubmissionFactory.create()

        assert not submission.is_authenticated

        with self.assertRaises(PrefillSkipped):
            self.plugin.get_prefill_values(submission, attributes)

    def test_prefill_values_for_gemachtigde_by_bsn(self):
        response_content = self.extract_soap_response(
            "stuf_bg/tests/responses/StufBgResponse.xml",
            self.stuf_bg_service,
        )

        # validate response
        self.assertSoapBodyIsValid(response_content)

        client_patcher = self.mock_stufbg_client(response_content)
        self.addCleanup(client_patcher.stop)
        attributes = [c.value for c in FieldChoices]
        submission = SubmissionFactory.create(
            auth_info__value="111111111",
            auth_info__is_digid_machtigen=True,
            auth_info__legal_subject_identifier_value="999990676",
        )

        values = self.plugin.get_prefill_values(
            submission, attributes, IdentifierRoles.authorizee
        )

        self.assertEqual(values["bsn"], "999992314")
        self.assertEqual(values["voornamen"], "Media")
        self.assertEqual(values["geslachtsnaam"], "Maykin")
        self.assertEqual(values["straatnaam"], "Keizersgracht")
        self.assertEqual(values["huisnummer"], "117")
        self.assertEqual(values["huisletter"], "A")
        self.assertEqual(values["huisnummertoevoeging"], "B")
        self.assertEqual(values["postcode"], "1015 CJ")
        self.assertEqual(values["woonplaatsNaam"], "Amsterdam")

    def test_extract_authorizee_identifier_value(self):
        cases = (
            # new auth context data approach
            (
                SubmissionFactory.create(
                    auth_info__is_digid_machtigen=True,
                    auth_info__legal_subject_identifier_value="999333666",
                ),
                "999333666",
            ),
            # new auth context data, but not a BSN
            (
                SubmissionFactory.create(
                    auth_info__is_eh_bewindvoering=True,
                    auth_info__legal_subject_identifier_value="12345678",
                ),
                None,
            ),
        )
        for submission, expected in cases:
            with self.subTest(auth_context=submission.auth_info.to_auth_context_data()):
                identifier_value = self.plugin.get_identifier_value(
                    submission, IdentifierRoles.authorizee
                )

                self.assertEqual(identifier_value, expected)


class StufBGHelpersTests(StUFBGAssertionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.stuf_bg_service = StufServiceFactory.create()

    def test_helper_is_object_not_found_response(self):
        with self.subTest("found"):
            response_content = self.extract_soap_response(
                "stuf_bg/tests/responses/StufBgResponse.xml",
                self.stuf_bg_service,
            )
            xml_obj = self.extract_soap_body(response_content)

            # validate response
            self.assertSoapBodyIsValid(response_content)
            self.assertFalse(is_object_not_found_response(xml_obj))

        with self.subTest("not found"):
            response_content = self.extract_soap_response(
                "stuf_bg/tests/responses/StufBgNotFoundResponse.xml",
                self.stuf_bg_service,
            )
            xml_obj = self.extract_soap_body(response_content)

            # response validation not needed for the fault
            self.assertTrue(is_object_not_found_response(xml_obj))

        with self.subTest("other error"):
            response_content = self.extract_soap_response(
                "stuf_bg/tests/responses/StufBgErrorResponse.xml",
                self.stuf_bg_service,
            )
            xml_obj = self.extract_soap_body(response_content)

            # response validation not needed for the fault
            self.assertFalse(is_object_not_found_response(xml_obj))

    def test_helper_is_empty_wrapped_response(self):
        with self.subTest("empty"):
            response_content = self.extract_soap_response(
                "stuf_bg/tests/responses/StufBgNoObjectResponse.xml",
                self.stuf_bg_service,
            )
            xml_obj = self.extract_soap_body(response_content)

            self.assertSoapBodyIsValid(response_content)
            self.assertTrue(is_empty_wrapped_response(xml_obj))

        with self.subTest("not empty"):
            response_content = self.extract_soap_response(
                "stuf_bg/tests/responses/StufBgResponse.xml",
                self.stuf_bg_service,
            )
            xml_obj = self.extract_soap_body(response_content)

            # validate response
            self.assertSoapBodyIsValid(response_content)
            self.assertFalse(is_empty_wrapped_response(xml_obj))

        with self.subTest("other error"):
            response_content = self.extract_soap_response(
                "stuf_bg/tests/responses/StufBgErrorResponse.xml",
                self.stuf_bg_service,
            )
            xml_obj = self.extract_soap_body(response_content)

            # response validation not needed for the fault
            self.assertFalse(is_empty_wrapped_response(xml_obj))
