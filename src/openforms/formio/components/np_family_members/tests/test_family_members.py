import json
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from django.utils.html import format_html
from django.utils.translation import gettext as _

import requests_mock
from zds_client.oas import schema_fetcher
from zgw_consumers.test import mock_service_oas_get

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.brp.models import BRPConfig
from openforms.formio.service import get_dynamic_configuration
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.template import render_from_string
from soap.constants import EndpointType
from stuf.stuf_bg.models import StufBGConfig
from stuf.tests.factories import StufServiceFactory

from ..constants import FamilyMembersDataAPIChoices
from ..haal_centraal import get_np_children_haal_centraal
from ..models import FamilyMembersTypeConfig
from ..stuf_bg import get_np_children_stuf_bg

TEST_FILES = Path(__file__).parent.resolve() / "responses"


class FamilyMembersCustomFieldTypeTest(TestCase):
    def setUp(self):
        super().setUp()

        # ensure the schema cache is cleared before and after each test
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)

    @patch(
        "openforms.formio.components.custom.get_np_children_haal_centraal",
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
                },
            ],
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
        )
        formio_wrapper = (
            submission.submissionstep_set.get().form_step.form_definition.configuration_wrapper
        )

        with patch(
            "openforms.formio.components.custom.FamilyMembersTypeConfig.get_solo",
            return_value=FamilyMembersTypeConfig(
                data_api=FamilyMembersDataAPIChoices.haal_centraal
            ),
        ):
            updated_config_wrapper = get_dynamic_configuration(
                formio_wrapper,
                request=None,
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

    @patch(
        "openforms.formio.components.np_family_members.haal_centraal.BRPConfig.get_solo"
    )
    def test_get_children_haal_centraal(self, mock_brp_config_get_solo):
        service = ServiceFactory.build(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        mock_brp_config_get_solo.return_value = BRPConfig(brp_service=service)
        with (TEST_FILES / "op_2_children.json").open("r") as infile:
            json_response = json.load(infile)

        with requests_mock.Mocker() as m:
            mock_service_oas_get(
                m, url=service.api_root, service="personen", oas_url=service.oas
            )
            m.get(
                "https://personen/api/ingeschrevenpersonen/111222333/kinderen",
                status_code=200,
                json=json_response,
            )

            kids_choices = get_np_children_haal_centraal(bsn="111222333")

            self.assertEqual(2, len(kids_choices))
            self.assertEqual(("456789123", "Bolly van Doe"), kids_choices[0])
            self.assertEqual(("789123456", "Billy van Doe"), kids_choices[1])

    @patch(
        "openforms.formio.components.np_family_members.stuf_bg.StufBGConfig.get_solo"
    )
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

            kids_choices = get_np_children_stuf_bg(bsn="111222333")

            self.assertEqual(3, len(kids_choices))
            self.assertEqual(("456789123", "Bolly van Doe"), kids_choices[0])
            self.assertEqual(("789123456", "Billy van Doe"), kids_choices[1])
            self.assertEqual(("123456789", "Billy van Doe"), kids_choices[2])

    @patch(
        "openforms.formio.components.custom.FamilyMembersTypeConfig.get_solo",
        return_value=FamilyMembersTypeConfig(
            data_api=FamilyMembersDataAPIChoices.haal_centraal
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
                },
            ],
            auth_info=None,
        )
        formio_wrapper = (
            submission.submissionstep_set.get().form_step.form_definition.configuration_wrapper
        )

        updated_config_wrapper = get_dynamic_configuration(
            formio_wrapper,
            request=None,
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
