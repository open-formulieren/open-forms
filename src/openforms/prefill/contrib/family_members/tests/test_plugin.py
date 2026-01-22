from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.template import loader
from django.test import TestCase
from django.utils import timezone

import requests_mock
from freezegun import freeze_time
from lxml import etree
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.authentication.constants import AuthAttribute
from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.forms.tests.factories import FormVariableFactory
from openforms.logging.tests.utils import disable_timelinelog
from openforms.prefill.service import prefill_variables
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes
from stuf.constants import EndpointType
from stuf.stuf_bg.models import StufBGConfig
from stuf.tests.factories import StufServiceFactory
from stuf.xml import fromstring

from ....registry import register
from ..plugin import PLUGIN_IDENTIFIER

plugin = register[PLUGIN_IDENTIFIER]


class FamilyMembersPrefillPluginHCV2Tests(OFVCRMixin, TestCase):
    """This test case requires the HaalCentraal BRP API to be running.
    See the relevant Docker compose in the ``docker/`` folder.

    Note: please ensure that all patches to the test data have been applied. See the
    README.md file of the relevant container.
    """

    def setUp(self):
        super().setUp()

        hc_config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/",
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        )
        hc_config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=hc_config,
        )
        global_config = GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        )
        global_config_patcher = patch(
            "openforms.config.models.GlobalConfiguration.get_solo",
            return_value=global_config,
        )
        hc_config_patcher.start()
        global_config_patcher.start()
        self.addCleanup(hc_config_patcher.stop)
        self.addCleanup(global_config_patcher.stop)

    def test_partners_prefill_happy_flow(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="999970124",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "hc_prefill_partners_mutable",
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="hc_prefill_partners_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "hc_prefill_partners_mutable",
                "min_age": None,
                "max_age": None,
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        expected_data = [
            {
                "bsn": "999970136",
                "firstNames": "Pia",
                "initials": "P.",
                "affixes": "",
                "lastName": "Pauw",
                "dateOfBirth": "1989-04-01",
                "dateOfBirthPrecision": "date",
            }
        ]

        self.assertEqual(
            state.variables["hc_prefill_partners_mutable"].value, expected_data
        )
        self.assertEqual(
            state.variables["hc_prefill_partners_immutable"].value, expected_data
        )

    def test_children_prefill_happy_flow(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="999970124",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "hc_prefill_children_mutable",
                    "type": "children",
                    "label": "Children",
                },
            ],
        )
        FormVariableFactory.create(
            key="hc_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "mutable_data_form_variable": "hc_prefill_children_mutable",
                "type": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        expected_data = [
            {
                "bsn": "999970409",
                "firstNames": "Pero",
                "initials": "P.",
                "affixes": "van",
                "lastName": "Paassen",
                "dateOfBirth": "2023-02-01",
                "dateOfBirthPrecision": "date",
            },
            {
                "bsn": "999970161",
                "firstNames": "Peet",
                "initials": "P.",
                "affixes": "van",
                "lastName": "Paassen",
                "dateOfBirth": "2018-12-01",
                "dateOfBirthPrecision": "date",
            },
            {
                "bsn": "999970173",
                "firstNames": "Pelle",
                "initials": "P.",
                "affixes": "van",
                "lastName": "Paassen",
                "dateOfBirth": "2017-09-01",
                "dateOfBirthPrecision": "date",
            },
            {
                "bsn": "999970185",
                "firstNames": "Pep",
                "initials": "P.",
                "affixes": "van",
                "lastName": "Paassen",
                "dateOfBirth": "2016-05-01",
                "dateOfBirthPrecision": "date",
            },
        ]

        self.assertEqual(
            state.variables["hc_prefill_children_mutable"].value, expected_data
        )
        self.assertEqual(
            state.variables["hc_prefill_children_immutable"].value, expected_data
        )

    def test_children_filtered_by_age(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="999970124",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "hc_prefill_children_mutable",
                    "type": "children",
                    "label": "Children",
                },
            ],
        )
        FormVariableFactory.create(
            key="hc_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "mutable_data_form_variable": "hc_prefill_children_mutable",
                "type": "children",
                "min_age": 8,
                "max_age": 16,
            },
        )

        with freeze_time("2025-04-25T18:00:00+01:00"):
            prefill_variables(submission=submission)

        state = submission.load_submission_value_variables_state()

        expected_data = [
            {
                "bsn": "999970185",
                "firstNames": "Pep",
                "initials": "P.",
                "affixes": "van",
                "lastName": "Paassen",
                "dateOfBirth": "2016-05-01",
                "dateOfBirthPrecision": "date",
            }
        ]

        self.assertEqual(
            state.variables["hc_prefill_children_mutable"].value, expected_data
        )
        self.assertEqual(
            state.variables["hc_prefill_children_immutable"].value, expected_data
        )

    def test_children_deceased(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="999970124",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "hc_prefill_children_mutable",
                    "type": "children",
                    "label": "Children",
                },
            ],
        )
        FormVariableFactory.create(
            key="hc_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "mutable_data_form_variable": "hc_prefill_children_mutable",
                "type": "children",
                "min_age": None,
                "max_age": None,
                "include_deceased": False,
            },
        )

        with freeze_time("2025-04-25T18:00:00+01:00"):
            prefill_variables(submission=submission)

        state = submission.load_submission_value_variables_state()

        expected_data = [
            {
                "bsn": "999970409",
                "firstNames": "Pero",
                "initials": "P.",
                "affixes": "van",
                "lastName": "Paassen",
                "dateOfBirth": "2023-02-01",
                "dateOfBirthPrecision": "date",
            },
            {
                "bsn": "999970161",
                "firstNames": "Peet",
                "initials": "P.",
                "affixes": "van",
                "lastName": "Paassen",
                "dateOfBirth": "2018-12-01",
                "dateOfBirthPrecision": "date",
            },
            {
                "bsn": "999970185",
                "firstNames": "Pep",
                "initials": "P.",
                "affixes": "van",
                "lastName": "Paassen",
                "dateOfBirth": "2016-05-01",
                "dateOfBirthPrecision": "date",
            },
        ]

        self.assertEqual(
            state.variables["hc_prefill_children_mutable"].value, expected_data
        )
        self.assertEqual(
            state.variables["hc_prefill_children_immutable"].value, expected_data
        )


PATH_XSDS = (Path(settings.BASE_DIR) / "src" / "stuf" / "stuf_bg" / "xsd").resolve()
STUF_BG_XSD = PATH_XSDS / "bg0310" / "vraagAntwoord" / "bg0310_namespace.xsd"


def _extract_soap_body(full_doc: str | bytes):
    doc = fromstring(full_doc)
    soap_body = doc.xpath(
        "soapenv:Body",
        namespaces={"soapenv": "http://www.w3.org/2003/05/soap-envelope"},
    )[0].getchildren()[0]
    return soap_body


@lru_cache
def _stuf_bg_xmlschema_doc():
    # don't add the etree.XMLSchema construction to this; it's an object
    # that contains state like error_log

    with STUF_BG_XSD.open("r") as infile:
        return etree.parse(infile)


def _stuf_bg_response(service, soap_response_template):
    response_body = bytes(
        loader.render_to_string(
            f"family_members/tests/responses/{soap_response_template}",
            context={
                "referentienummer": "38151851-0fe9-4463-ba39-416042b8f406",
                "tijdstip_bericht": timezone.now().strftime("%Y%m%d%H%M%S"),
                "zender_organisatie": service.ontvanger_organisatie,
                "zender_applicatie": service.ontvanger_applicatie,
                "zender_administratie": service.ontvanger_administratie,
                "zender_gebruiker": service.ontvanger_gebruiker,
                "ontvanger_organisatie": service.zender_organisatie,
                "ontvanger_applicatie": service.zender_applicatie,
                "ontvanger_administratie": service.zender_administratie,
                "ontvanger_gebruiker": service.zender_gebruiker,
            },
        ),
        encoding="utf-8",
    )
    # assert this mocked response is valid
    xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())
    xmlschema.assert_(_extract_soap_body(response_body))
    return response_body


@disable_timelinelog()
class FamilyMembersPrefillPluginStufBgTests(TestCase):
    def setUp(self):
        super().setUp()

        self.stuf_bg_service = StufServiceFactory.build()
        stuf_bg_config = StufBGConfig(service=self.stuf_bg_service)
        stuf_bg_config_patcher = patch(
            "stuf.stuf_bg.client.StufBGConfig.get_solo",
            return_value=stuf_bg_config,
        )
        global_config = GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.stuf_bg
        )
        global_config_patcher = patch(
            "openforms.config.models.GlobalConfiguration.get_solo",
            return_value=global_config,
        )

        stuf_bg_config_patcher.start()
        global_config_patcher.start()
        self.addCleanup(stuf_bg_config_patcher.stop)
        self.addCleanup(global_config_patcher.stop)

    def test_partners_prefill_happy_flow(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "stuf_bg_partners_mutable",
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="stuf_bg_partners_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "stuf_bg_partners_mutable",
                "min_age": None,
                "max_age": None,
            },
        )

        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=_stuf_bg_response(
                    self.stuf_bg_service, "stuf_bg_one_partner.xml"
                ),
            )
            prefill_variables(submission=submission)

        # validate request
        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())
        request_body = m.last_request.body
        soap_body = _extract_soap_body(request_body)
        xmlschema.assert_(soap_body)

        state = submission.load_submission_value_variables_state()

        expected_data = [
            {
                "bsn": "123123123",
                "firstNames": "Belly",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "1985-06-15",
                "deceased": None,
            }
        ]

        self.assertEqual(
            state.variables["stuf_bg_partners_mutable"].value, expected_data
        )
        self.assertEqual(
            state.variables["stuf_bg_partners_immutable"].value, expected_data
        )

    def test_children_prefill_happy_flow(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "stuf_bg_prefill_children_mutable",
                    "type": "children",
                    "label": "Children",
                },
            ],
        )
        FormVariableFactory.create(
            key="stuf_bg_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "stuf_bg_prefill_children_mutable",
                "min_age": None,
                "max_age": None,
            },
        )

        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=_stuf_bg_response(self.stuf_bg_service, "stuf_bg_children.xml"),
            )
            prefill_variables(submission=submission)

        # validate request
        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())
        request_body = m.last_request.body
        soap_body = _extract_soap_body(request_body)
        xmlschema.assert_(soap_body)

        state = submission.load_submission_value_variables_state()
        expected_data = [
            {
                "bsn": "456789123",
                "firstNames": "Bolly",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "1999-06-15",
                "deceased": False,
            },
            {
                "bsn": "789123456",
                "firstNames": "Billy",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "1998-07-16",
                "deceased": False,
            },
            {
                "bsn": "123456789",
                "firstNames": "Billy",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "",
                "deceased": False,
            },
            {
                "bsn": "789123543",
                "firstNames": "Other",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doens",
                "dateOfBirth": "1998-07-16",
                "deceased": True,
            },
        ]

        self.assertEqual(
            state.variables["stuf_bg_prefill_children_mutable"].value, expected_data
        )
        self.assertEqual(
            state.variables["stuf_bg_prefill_children_immutable"].value, expected_data
        )

    def test_children_with_deceased_filter(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "stuf_bg_prefill_children_mutable",
                    "type": "children",
                    "label": "Children",
                },
            ],
        )
        FormVariableFactory.create(
            key="stuf_bg_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "stuf_bg_prefill_children_mutable",
                "min_age": None,
                "max_age": None,
                "include_deceased": False,
            },
        )

        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=_stuf_bg_response(self.stuf_bg_service, "stuf_bg_children.xml"),
            )
            prefill_variables(submission=submission)

        # validate request
        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())
        request_body = m.last_request.body
        soap_body = _extract_soap_body(request_body)
        xmlschema.assert_(soap_body)

        state = submission.load_submission_value_variables_state()

        expected_data = [
            {
                "bsn": "456789123",
                "firstNames": "Bolly",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "1999-06-15",
                "deceased": False,
            },
            {
                "bsn": "789123456",
                "firstNames": "Billy",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "1998-07-16",
                "deceased": False,
            },
            # included because no age filter boundaries are provided, so even the
            # children without known DOB are returned
            {
                "bsn": "123456789",
                "firstNames": "Billy",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "",
                "deceased": False,
            },
        ]

        self.assertEqual(
            state.variables["stuf_bg_prefill_children_mutable"].value, expected_data
        )
        self.assertEqual(
            state.variables["stuf_bg_prefill_children_immutable"].value, expected_data
        )

    def test_children_with_incomplete_dateOfBirth_are_shown_when_no_filter(self):
        """
        Children with incomplete data for date of birth.
        All the children should be sent to the frontend when there is no filtering on age
        required.
        """
        submission = SubmissionFactory.from_components(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "stuf_bg_prefill_children_mutable",
                    "type": "children",
                    "label": "Children",
                },
            ],
        )
        FormVariableFactory.create(
            key="stuf_bg_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "stuf_bg_prefill_children_mutable",
                "min_age": None,
                "max_age": None,
            },
        )

        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=_stuf_bg_response(
                    self.stuf_bg_service,
                    "stuf_bg_children_incomplete_date_of_birth.xml",
                ),
            )
            prefill_variables(submission=submission)

        # validate request
        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())
        request_body = m.last_request.body
        soap_body = _extract_soap_body(request_body)
        xmlschema.assert_(soap_body)

        state = submission.load_submission_value_variables_state()

        expected_data = [
            {
                "bsn": "456789123",
                "firstNames": "Bolly",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "1999-06-15",
                "deceased": False,
            },
            {
                "bsn": "789123456",
                "firstNames": "Billy",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "1985",
                "deceased": False,
            },
            {
                "bsn": "123456788",
                "firstNames": "Billy",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "198503",
                "deceased": False,
            },
            {
                "bsn": "167556788",
                "firstNames": "Billy",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "",
                "deceased": False,
            },
        ]

        self.assertEqual(
            state.variables["stuf_bg_prefill_children_immutable"].value, expected_data
        )

        # Partial dates will be converted to empty strings for the partner component.
        expected_data[1]["dateOfBirth"] = ""
        expected_data[2]["dateOfBirth"] = ""

        self.assertEqual(
            state.variables["stuf_bg_prefill_children_mutable"].value, expected_data
        )

    def test_children_with_incomplete_dateOfBirth_are_not_shown_when_filter(self):
        """
        Children with incomplete data for date of birth.
        Only the children that have a complete (ISO 8601) date should be filtered and sent
        to the frontend when they need filtering on age.
        """
        submission = SubmissionFactory.from_components(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "stuf_bg_prefill_children_mutable",
                    "type": "children",
                    "label": "Children",
                },
            ],
        )
        FormVariableFactory.create(
            key="stuf_bg_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "stuf_bg_prefill_children_mutable",
                "min_age": 18,
                "max_age": 30,
            },
        )

        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=_stuf_bg_response(
                    self.stuf_bg_service,
                    "stuf_bg_children_incomplete_date_of_birth.xml",
                ),
            )
            prefill_variables(submission=submission)

        # validate request
        xmlschema = etree.XMLSchema(_stuf_bg_xmlschema_doc())
        request_body = m.last_request.body
        soap_body = _extract_soap_body(request_body)
        xmlschema.assert_(soap_body)

        state = submission.load_submission_value_variables_state()

        expected_data = [
            {
                "bsn": "456789123",
                "firstNames": "Bolly",
                "initials": "K",
                "affixes": "van",
                "lastName": "Doe",
                "dateOfBirth": "1999-06-15",
                "deceased": False,
            },
        ]

        self.assertEqual(
            state.variables["stuf_bg_prefill_children_mutable"].value, expected_data
        )
        self.assertEqual(
            state.variables["stuf_bg_prefill_children_immutable"].value, expected_data
        )
