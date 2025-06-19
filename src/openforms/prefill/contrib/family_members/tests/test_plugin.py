from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from freezegun import freeze_time
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
from openforms.template import render_from_string
from openforms.utils.tests.vcr import OFVCRMixin
from stuf.constants import EndpointType
from stuf.stuf_bg.models import StufBGConfig
from stuf.tests.factories import StufServiceFactory

from ....registry import register
from ..plugin import PLUGIN_IDENTIFIER

plugin = register[PLUGIN_IDENTIFIER]


TEST_FILES = Path(__file__).parent.resolve() / "responses"
VCR_TEST_FILES = Path(__file__).parent / "files"


class FamilyMembersPrefillPluginHCV2Tests(OFVCRMixin, TestCase):
    """This test case requires the HaalCentraal BRP API to be running.
    See the relevant Docker compose in the ``docker/`` folder.

    Note: please ensure that all patches to the test data have been applied. See the
    README.md file of the relevant container.
    """

    VCR_TEST_FILES = VCR_TEST_FILES

    def setUp(self):
        super().setUp()

        hc_config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/"
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
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="hc_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
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
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="hc_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
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
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="hc_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
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
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "stuf_bg_partners_mutable",
                "min_age": None,
                "max_age": None,
            },
        )

        soap_response_template = (TEST_FILES / "stuf_bg_one_partner.xml").read_text()
        response_content = render_from_string(soap_response_template, {}).encode(
            "utf-8"
        )

        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=response_content,
            )
            prefill_variables(submission=submission)

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
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="stuf_bg_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "stuf_bg_prefill_children_mutable",
                "min_age": None,
                "max_age": None,
            },
        )

        soap_response_template = (TEST_FILES / "stuf_bg_children.xml").read_text()
        response_content = render_from_string(soap_response_template, {}).encode(
            "utf-8"
        )
        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=response_content,
            )
            prefill_variables(submission=submission)

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
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="stuf_bg_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "stuf_bg_prefill_children_mutable",
                "min_age": None,
                "max_age": None,
                "include_deceased": False,
            },
        )

        soap_response_template = (TEST_FILES / "stuf_bg_children.xml").read_text()
        response_content = render_from_string(soap_response_template, {}).encode(
            "utf-8"
        )
        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=response_content,
            )
            prefill_variables(submission=submission)

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
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="stuf_bg_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "stuf_bg_prefill_children_mutable",
                "min_age": None,
                "max_age": None,
            },
        )

        soap_response_template = (
            TEST_FILES / "stuf_bg_children_incomplete_date_of_birth.xml"
        ).read_text()
        response_content = render_from_string(soap_response_template, {}).encode(
            "utf-8"
        )
        with requests_mock.Mocker() as m:
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=response_content,
            )
            prefill_variables(submission=submission)

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
                "dateOfBirth": "1985-03",
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
            state.variables["stuf_bg_prefill_children_mutable"].value, expected_data
        )
        self.assertEqual(
            state.variables["stuf_bg_prefill_children_immutable"].value, expected_data
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
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="stuf_bg_prefill_children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "stuf_bg_prefill_children_mutable",
                "min_age": 18,
                "max_age": 30,
            },
        )

        soap_response_template = (
            TEST_FILES / "stuf_bg_children_incomplete_date_of_birth.xml"
        ).read_text()
        response_content = render_from_string(soap_response_template, {}).encode(
            "utf-8"
        )

        with requests_mock.Mocker() as m, freeze_time("2025-04-25T18:00:00+01:00"):
            m.post(
                self.stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=response_content,
            )
            prefill_variables(submission=submission)

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
