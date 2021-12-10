from unittest.mock import patch

from django.template import loader
from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory
from stuf.stuf_bg.models import StufBGConfig
from stuf.tests.factories import StufServiceFactory

from ....co_sign import add_co_sign_representation
from ....models import PrefillConfig
from ....registry import register

plugin = register["stufbg"]


class CoSignPrefillTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        config = PrefillConfig.get_solo()
        config.default_person_plugin = plugin.identifier
        config.save()

        stuf_bg_service = StufServiceFactory.create()
        config = StufBGConfig.get_solo()
        config.service = stuf_bg_service
        config.save()

    def test_store_names_on_co_sign_auth(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": plugin.identifier,
                "identifier": "999992314",
                "fields": {},
            }
        )
        return_value = loader.render_to_string(
            "stuf_bg/tests/responses/StufBgResponse.xml"
        )

        with patch(
            "stuf.stuf_bg.client.StufBGClient.get_values_for_attributes",
            return_value=return_value,
        ) as m:
            add_co_sign_representation(submission, plugin.requires_auth)

        submission.refresh_from_db()
        self.assertEqual(
            submission.co_sign_data,
            {
                "plugin": plugin.identifier,
                "identifier": "999992314",
                "representation": "M. Maykin",
                "fields": {
                    "voornamen": "Media",
                    "geslachtsnaam": "Maykin",
                },
            },
        )
