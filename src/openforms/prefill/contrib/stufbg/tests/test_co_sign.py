from unittest.mock import patch

from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ....co_sign import add_co_sign_representation
from ....models import PrefillConfig
from ....registry import register
from .utils import mock_stufbg_client

plugin = register["stufbg"]


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
