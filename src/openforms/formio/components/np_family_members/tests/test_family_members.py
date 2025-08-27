import json
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, tag
from django.utils.html import format_html
from django.utils.translation import gettext as _

import requests_mock
from zgw_consumers.test.factories import ServiceFactory

from openforms.authentication.service import AuthAttribute
from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.formio.service import get_dynamic_configuration
from openforms.logging.tests.utils import disable_timelinelog
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.template import render_from_string
from stuf.constants import EndpointType
from stuf.stuf_bg.models import StufBGConfig
from stuf.tests.factories import StufServiceFactory

from ..haal_centraal import get_np_family_members_haal_centraal
from ..stuf_bg import get_np_family_members_stuf_bg

TEST_FILES = Path(__file__).parent.resolve() / "responses"


@disable_timelinelog()
class FamilyMembersCustomFieldTypeTest(TestCase):
    @patch(
        "openforms.formio.components.custom.get_np_family_members_haal_centraal",
        return_value=[("222333444", "Billy Doe"), ("333444555", "Jane Doe")],
    )
    def test_get_values_for_custom_field(self, mock_get_np_children):
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
            auth_info__value="111222333",
        )
        formio_wrapper = submission.submissionstep_set.get().form_step.form_definition.configuration_wrapper

        with patch(
            "openforms.formio.components.custom.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
            ),
        ):
            updated_config_wrapper = get_dynamic_configuration(
                formio_wrapper,
                submission=submission,
            )

        rewritten_component = updated_config_wrapper["npFamilyMembers"]
        self.assertEqual("selectboxes", rewritten_component["type"])
        self.assertFalse(rewritten_component["fieldSet"])
        self.assertFalse(rewritten_component["inline"])
        self.assertEqual("checkbox", rewritten_component["inputType"])
        self.assertEqual(2, len(rewritten_component["values"]))
        self.assertEqual(
            rewritten_component["values"][0],
            {"value": "222333444", "label": "Billy Doe"},
        )
        self.assertEqual(
            rewritten_component["values"][1],
            {"value": "333444555", "label": "Jane Doe"},
        )

    @patch("openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo")
    def test_get_children_haal_centraal(self, mock_brp_config_get_solo):
        mock_brp_config_get_solo.return_value = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="https://personen/api/",
            )
        )
        with (TEST_FILES / "op_2_children.json").open("r") as infile:
            json_response = json.load(infile)

        with requests_mock.Mocker() as m:
            m.get(
                "https://personen/api/ingeschrevenpersonen/111222333/kinderen",
                status_code=200,
                json=json_response,
            )

            kids_choices = get_np_family_members_haal_centraal(
                bsn="111222333", include_children=True, include_partners=False
            )

            self.assertEqual(2, len(kids_choices))
            self.assertEqual(("456789123", "Bolly van Doe"), kids_choices[0])
            self.assertEqual(("789123456", "Billy van Doe"), kids_choices[1])

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
        formio_wrapper = submission.submissionstep_set.get().form_step.form_definition.configuration_wrapper

        updated_config_wrapper = get_dynamic_configuration(
            formio_wrapper,
            submission=submission,
        )

        rewritten_component = updated_config_wrapper["npFamilyMembers"]
        self.assertEqual(rewritten_component["type"], "content")
        self.assertEqual(
            rewritten_component["html"],
            format_html(
                "<p>{message}</p>",
                message=_("Selecting family members is currently not available."),
            ),
        )
