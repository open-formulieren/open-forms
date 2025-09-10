from unittest.mock import patch

from django.test import TestCase

import requests_mock
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.contrib.haal_centraal.tests.utils import load_json_mock
from openforms.submissions.tests.factories import SubmissionFactory

from ....co_sign import add_co_sign_representation
from ....models import PrefillConfig
from ....registry import register
from ..plugin import PLUGIN_IDENTIFIER

plugin = register[PLUGIN_IDENTIFIER]

AUTH_ATTRIBUTE = next(attr for attr in plugin.requires_auth)


class CoSignPrefillTests:
    """
    Mixin defining the actual tests to run for a particular client version.

    All client versions must support this set of functionality.

    You must implement the classmethod ``setUpTestData`` to create the relevant service,
    for which you can then mock the API calls.
    """

    # specify in subclasses
    version: BRPVersions

    def setUp(self):
        super().setUp()  # type: ignore

        # mock out django-solo interface (we don't have to deal with caches then)
        co_sign_config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        co_sign_config_patcher.start()
        self.addCleanup(co_sign_config_patcher.stop)  # type: ignore

        # set up patcher for the configuration
        hc_config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="https://personen/api/",
            ),
            brp_personen_version=self.version,
        )
        hc_config_patcher = patch(
            "openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo",
            return_value=hc_config,
        )
        hc_config_patcher.start()
        self.addCleanup(hc_config_patcher.stop)  # type: ignore

        # prepare a requests mock instance to wire up the mocks
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)  # type: ignore

    def test_store_names_on_co_sign_auth(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "version": "v1",
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "co_sign_auth_attribute": "bsn",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, AUTH_ATTRIBUTE)

        submission.refresh_from_db()
        expected = {
            "version": "v1",
            "plugin": plugin.identifier,
            "identifier": "999990676",
            "co_sign_auth_attribute": "bsn",
            "representation": "C. F. Wiegman",
            "fields": {
                "naam.voornamen": "Cornelia Francisca",
                "naam.voorvoegsel": "",
                "naam.voorletters": "C. F.",
                "naam.geslachtsnaam": "Wiegman",
            },
        }
        self.assertEqual(submission.co_sign_data, expected)  # type: ignore

    def test_incomplete_data_returned(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "version": "v1",
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "co_sign_auth_attribute": "bsn",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, AUTH_ATTRIBUTE)

        submission.refresh_from_db()
        expected = {
            "version": "v1",
            "plugin": plugin.identifier,
            "identifier": "999990676",
            "representation": "",
            "co_sign_auth_attribute": "bsn",
            "fields": {},
        }
        self.assertEqual(submission.co_sign_data, expected)  # type: ignore


class CoSignPrefillV1Tests(CoSignPrefillTests, TestCase):
    version = BRPVersions.v13

    def test_store_names_on_co_sign_auth(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1-full.json"),
        )
        super().test_store_names_on_co_sign_auth()

    def test_incomplete_data_returned(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1-incomplete.json"),
        )
        super().test_incomplete_data_returned()


class CoSignPrefillV2Tests(CoSignPrefillTests, TestCase):
    version = BRPVersions.v20

    def test_store_names_on_co_sign_auth(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_store_names_on_co_sign_auth()

    def test_incomplete_data_returned(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-incomplete.json"),
        )
        super().test_incomplete_data_returned()


class CoSignPrefillEmptyConfigTests(TestCase):
    def setUp(self):
        super().setUp()

        # mock out django-solo interface (we don't have to deal with caches then)
        config_patcher = patch(
            "openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                brp_personen_version="", brp_personen_service=None
            ),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

        co_sign_config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        co_sign_config_patcher.start()
        self.addCleanup(co_sign_config_patcher.stop)  # type: ignore

    def test_store_names_on_co_sign_auth(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "version": "v1",
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "co_sign_auth_attribute": "bsn",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, AUTH_ATTRIBUTE)

        submission.refresh_from_db()
        expected = {
            "version": "v1",
            "plugin": plugin.identifier,
            "identifier": "999990676",
            "co_sign_auth_attribute": "bsn",
            "representation": "",
            "fields": {},
        }
        self.assertEqual(submission.co_sign_data, expected)
