from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, tag
from django.utils.html import format_html
from django.utils.translation import gettext as _

import requests_mock
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from formio_types import Content, Option, Selectboxes
from openforms.authentication.service import AuthAttribute
from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.logging.tests.utils import disable_timelinelog
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.template import render_from_string
from openforms.utils.tests.vcr import OFVCRMixin
from stuf.constants import EndpointType
from stuf.stuf_bg.models import StufBGConfig
from stuf.tests.factories import StufServiceFactory

from ...components.np_family_members.haal_centraal import (
    get_np_family_members_haal_centraal,
)
from ...components.np_family_members.stuf_bg import get_np_family_members_stuf_bg
from ...service import get_dynamic_configuration

TEST_FILES = Path(__file__).parent.resolve() / "responses"


@disable_timelinelog()
class FamilyMembersCustomFieldTypeTest(OFVCRMixin, TestCase):
    def setUp(self):
        super().setUp()

        # set up patcher for the configuration
        config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/",
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        )
        config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=config,
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

    def test_get_values_for_custom_field(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "npFamilyMembers",
                    "type": "npFamilyMembers",
                    "label": "FamilyMembers",
                    "values": [{"label": "", "value": ""}],
                    "includePartners": False,
                    "includeChildren": True,
                },
            ],
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="999990676",
        )
        step = submission.submissionstep_set.get()
        assert step.form_step is not None
        formio_config = step.form_step.form_definition.formio_config

        with patch(
            "openforms.formio.components.custom.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
            ),
        ):
            updated_config = get_dynamic_configuration(
                formio_config, submission=submission
            )

        rewritten_component = updated_config["npFamilyMembers"]
        assert isinstance(rewritten_component, Selectboxes)

        expected_options = [
            Option(value="999991760", label="Angélie Francisca Holthuizen"),
            Option(value="999993392", label="Margaretha Holthuizen"),
            Option(value="999991978", label="Adrianus Holthuizen"),
        ]
        self.assertEqual(rewritten_component.values, expected_options)

    def test_get_children_haal_centraal(self):
        kids_choices = get_np_family_members_haal_centraal(
            bsn="999990676", include_children=True, include_partners=False
        )

        self.assertEqual(3, len(kids_choices))
        self.assertEqual(("999991760", "Angélie Francisca Holthuizen"), kids_choices[0])
        self.assertEqual(("999993392", "Margaretha Holthuizen"), kids_choices[1])
        self.assertEqual(("999991978", "Adrianus Holthuizen"), kids_choices[2])

    @patch("stuf.stuf_bg.client.StufBGConfig.get_solo")
    def test_get_children_stuf_bg(self, mock_stufbg_config_get_solo):
        stuf_bg_service = StufServiceFactory.build()
        mock_stufbg_config_get_solo.return_value = StufBGConfig(service=stuf_bg_service)
        soap_response_template = (TEST_FILES / "stuf_bg_2_children.xml").read_text()
        response_content = render_from_string(soap_response_template, {}).encode(
            "utf-8"
        )

        with requests_mock.Mocker() as m:
            m.post(
                stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=response_content,
            )

            kids_choices = get_np_family_members_stuf_bg(
                bsn="111222333", include_children=True, include_partners=False
            )

            self.assertEqual(3, len(kids_choices))
            self.assertEqual(("456789123", "Bolly van Doe"), kids_choices[0])
            self.assertEqual(("789123456", "Billy van Doe"), kids_choices[1])
            self.assertEqual(("123456789", "Billy van Doe"), kids_choices[2])

    @patch("stuf.stuf_bg.client.StufBGConfig.get_solo")
    def test_get_partners_stuf_bg(self, mock_stufbg_config_get_solo):
        stuf_bg_service = StufServiceFactory.build()
        mock_stufbg_config_get_solo.return_value = StufBGConfig(service=stuf_bg_service)
        soap_response_template = (TEST_FILES / "stuf_bg_family_members.xml").read_text()
        response_content = render_from_string(soap_response_template, {}).encode(
            "utf-8"
        )

        with requests_mock.Mocker() as m:
            m.post(
                stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=response_content,
            )

            partners_choices = get_np_family_members_stuf_bg(
                bsn="111222333", include_children=False, include_partners=True
            )

            self.assertEqual(2, len(partners_choices))
            self.assertEqual(("123123123", "Belly van Doe"), partners_choices[0])
            self.assertEqual(("456456456", "Bully van Doe"), partners_choices[1])

    @tag("gh-3864")
    @patch("stuf.stuf_bg.client.StufBGConfig.get_solo")
    def test_get_single_partner_stuf_bg(self, mock_stufbg_config_get_solo):
        stuf_bg_service = StufServiceFactory.build()
        mock_stufbg_config_get_solo.return_value = StufBGConfig(service=stuf_bg_service)
        soap_response_template = (TEST_FILES / "stuf_bg_one_partner.xml").read_text()
        response_content = render_from_string(soap_response_template, {}).encode(
            "utf-8"
        )

        with requests_mock.Mocker() as m:
            m.post(
                stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=response_content,
            )

            partners_choices = get_np_family_members_stuf_bg(
                bsn="111222333", include_children=False, include_partners=True
            )

            self.assertEqual(1, len(partners_choices))
            self.assertEqual(("123123123", "Belly van Doe"), partners_choices[0])

    @patch("stuf.stuf_bg.client.StufBGConfig.get_solo")
    def test_get_family_memebers_stuf_bg(self, mock_stufbg_config_get_solo):
        stuf_bg_service = StufServiceFactory.build()
        mock_stufbg_config_get_solo.return_value = StufBGConfig(service=stuf_bg_service)
        soap_response_template = (TEST_FILES / "stuf_bg_family_members.xml").read_text()
        response_content = render_from_string(soap_response_template, {}).encode(
            "utf-8"
        )

        with requests_mock.Mocker() as m:
            m.post(
                stuf_bg_service.get_endpoint(type=EndpointType.vrije_berichten),
                content=response_content,
            )

            family_choices = get_np_family_members_stuf_bg(
                bsn="111222333", include_children=True, include_partners=True
            )

            self.assertEqual(4, len(family_choices))
            self.assertEqual(("456789123", "Bolly van Doe"), family_choices[0])
            self.assertEqual(("789123456", "Billy van Doe"), family_choices[1])
            self.assertEqual(("123123123", "Belly van Doe"), family_choices[2])
            self.assertEqual(("456456456", "Bully van Doe"), family_choices[3])

    @patch(
        "openforms.formio.components.custom.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        ),
    )
    def test_no_crash_when_no_bsn_available(self, mock_get_solo):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "npFamilyMembers",
                    "type": "npFamilyMembers",
                    "label": "FamilyMembers",
                    "values": [{"label": "", "value": ""}],
                    "includeChildren": True,
                    "includePartners": False,
                },
            ],
            auth_info=None,
        )
        step = submission.submissionstep_set.get()
        assert step.form_step is not None
        formio_config = step.form_step.form_definition.formio_config

        updated_config = get_dynamic_configuration(formio_config, submission=submission)

        rewritten_component = updated_config["npFamilyMembers"]
        assert isinstance(rewritten_component, Content)
        self.assertEqual(
            rewritten_component.html,
            format_html(
                "<p>{message}</p>",
                message=_("Selecting family members is currently not available."),
            ),
        )
