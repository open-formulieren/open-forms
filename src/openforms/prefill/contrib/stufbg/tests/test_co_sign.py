from unittest.mock import patch

from django.template import loader
from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ....co_sign import add_co_sign_representation
from ....models import PrefillConfig
from ....registry import register

plugin = register["stufbg"]


def mock_stufbg_client(template: str):
    patcher = patch("openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo")
    mock_client = patcher.start()
    get_values_for_attributes_mock = (
        mock_client.return_value.get_client.return_value.get_values_for_attributes
    )
    get_values_for_attributes_mock.return_value = loader.render_to_string(
        f"stuf_bg/tests/responses/{template}"
    )
    return patcher


class CoSignPrefillTests(TestCase):
    def setUp(self):
        super().setUp()

        # mock out django-solo interface (we don't have to deal with caches then)
        config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        # mock out StufBG client
        client_patcher = mock_stufbg_client("StufBgResponse.xml")
        self.addCleanup(client_patcher.stop)

    def test_store_names_on_co_sign_auth(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": plugin.identifier,
                "identifier": "999992314",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, plugin.requires_auth)

        submission.refresh_from_db()
        self.assertEqual(
            submission.co_sign_data,
            {
                "plugin": plugin.identifier,
                "identifier": "999992314",
                "fields": {
                    "voornamen": "Media",
                    "geslachtsnaam": "Maykin",
                },
            },
        )
