from unittest.mock import patch

from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory
from stuf.stuf_bg.models import StufBGConfig
from stuf.stuf_bg.tests.utils import mock_stufbg_client
from stuf.tests.factories import StufServiceFactory

from ....co_sign import add_co_sign_representation
from ....models import PrefillConfig
from ....registry import register

plugin = register["stufbg"]

AUTH_ATTRIBUTE = next(attr for attr in plugin.requires_auth)


class CoSignPrefillTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.stuf_bg_service = StufServiceFactory.create()

    def setUp(self):
        super().setUp()

        # mock out django-solo interface (we don't have to deal with caches then)
        prefil_config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        prefil_config_patcher.start()
        self.addCleanup(prefil_config_patcher.stop)

        stufbg_config_patcher = patch(
            "openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo",
            return_value=StufBGConfig(service=self.stuf_bg_service),
        )
        stufbg_config_patcher.start()
        self.addCleanup(stufbg_config_patcher.stop)

        # mock out StufBG client
        client_patcher = mock_stufbg_client("StufBgResponse.xml")
        self.addCleanup(client_patcher.stop)

    def test_store_names_on_co_sign_auth(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "version": "v1",
                "plugin": plugin.identifier,
                "identifier": "999992314",
                "co_sign_auth_attribute": "bsn",
                "fields": {},
            }
        )
        add_co_sign_representation(submission, AUTH_ATTRIBUTE)

        submission.refresh_from_db()
        self.assertEqual(
            submission.co_sign_data,
            {
                "version": "v1",
                "plugin": plugin.identifier,
                "identifier": "999992314",
                "representation": "M. Maykin",
                "co_sign_auth_attribute": "bsn",
                "fields": {
                    "voornamen": "Media",
                    "geslachtsnaam": "Maykin",
                },
            },
        )
