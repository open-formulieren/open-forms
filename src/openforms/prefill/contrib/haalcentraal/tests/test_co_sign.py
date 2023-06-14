from unittest.mock import patch

from django.test import TestCase

import requests_mock

from openforms.prefill.contrib.haalcentraal.constants import HaalCentraalVersion
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ....co_sign import add_co_sign_representation
from ....models import PrefillConfig
from ....registry import register
from ..models import HaalCentraalConfig
from .utils import load_binary_mock, load_json_mock

plugin = register["haalcentraal"]


class BaseCoSignPrefillTests:
    class CoSignPrefillTests(TestCase):
        @classmethod
        def setUpTestData(cls):
            super().setUpTestData()

            cls.service = ServiceFactory.create(
                api_root="https://personen/api/",
                oas="https://personen/api/schema/openapi.yaml",
            )

        def setUp(self):
            super().setUp()

            # mock out django-solo interface (we don't have to deal with caches then)
            config_patcher = patch(
                "openforms.prefill.co_sign.PrefillConfig.get_solo",
                return_value=PrefillConfig(default_person_plugin=plugin.identifier),
            )
            config_patcher.start()
            self.addCleanup(config_patcher.stop)

        @requests_mock.Mocker()
        def test_store_names_on_co_sign_auth(self, m):
            m.get(
                "https://personen/api/schema/openapi.yaml?v=3",
                content=load_binary_mock(self.personen),
            )
            with patch(
                f"openforms.prefill.contrib.haalcentraal.client.{self.client}.find_person",
                return_value=load_json_mock(self.ingeschreven_personen),
            ):
                submission = SubmissionFactory.create(
                    co_sign_data={
                        "plugin": plugin.identifier,
                        "identifier": "999990676",
                        "fields": {},
                    }
                )

                add_co_sign_representation(submission, plugin.requires_auth)

                submission.refresh_from_db()
                self.assertEqual(
                    submission.co_sign_data,
                    {
                        "plugin": plugin.identifier,
                        "identifier": "999990676",
                        "representation": "C. F. Wiegman",
                        "fields": {
                            "naam.voornamen": "Cornelia Francisca",
                            "naam.voorvoegsel": "",
                            "naam.voorletters": "C. F.",
                            "naam.geslachtsnaam": "Wiegman",
                        },
                    },
                )

        @requests_mock.Mocker()
        def test_incomplete_data_returned(self, m):
            # the API should not leave out those fields, but just to be on the safe side,
            # anticipate it
            m.get(
                "https://personen/api/schema/openapi.yaml?v=3",
                content=load_binary_mock(self.personen),
            )
            with patch(
                f"openforms.prefill.contrib.haalcentraal.client.{self.client}.find_person",
                return_value=load_json_mock(self.ingeschreven_personen_incomplete),
            ):
                submission = SubmissionFactory.create(
                    co_sign_data={
                        "plugin": plugin.identifier,
                        "identifier": "999990676",
                        "fields": {},
                    }
                )

                add_co_sign_representation(submission, plugin.requires_auth)

                submission.refresh_from_db()
                self.assertEqual(
                    submission.co_sign_data,
                    {
                        "plugin": plugin.identifier,
                        "identifier": "999990676",
                        "representation": "",
                        "fields": {},
                    },
                )


class CoSignPrefillDefaultVersionTests(BaseCoSignPrefillTests.CoSignPrefillTests):
    def setUp(self):
        super().setUp()
        # mock out django-solo interface (we don't have to deal with caches then)

        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(service=self.service),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.client = "HaalCentraalV1Client"
        self.personen = "personen.yaml"
        self.ingeschreven_personen = "ingeschrevenpersonen.999990676.json"
        self.ingeschreven_personen_incomplete = (
            "ingeschrevenpersonen.999990676-incomplete.json"
        )


class CoSignPrefillV1Tests(BaseCoSignPrefillTests.CoSignPrefillTests):
    def setUp(self):
        super().setUp()
        # mock out django-solo interface (we don't have to deal with caches then)

        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                service=self.service, version=HaalCentraalVersion.haalcentraal13
            ),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.client = "HaalCentraalV1Client"
        self.personen = "personen.yaml"
        self.ingeschreven_personen = "ingeschrevenpersonen.999990676.json"
        self.ingeschreven_personen_incomplete = (
            "ingeschrevenpersonen.999990676-incomplete.json"
        )


class CoSignPrefillV2Tests(BaseCoSignPrefillTests.CoSignPrefillTests):
    def setUp(self):
        super().setUp()
        # mock out django-solo interface (we don't have to deal with caches then)

        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                service=self.service, version=HaalCentraalVersion.haalcentraal20
            ),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.client = "HaalCentraalV2Client"
        self.personen = "personen-v2.yaml"
        self.ingeschreven_personen = "personen-full-response.json"
        self.ingeschreven_personen_incomplete = "personen-incomplete.json"


class CoSignPrefillNoConfigTests(TestCase):
    def setUp(self):
        super().setUp()

        # mock out django-solo interface (we don't have to deal with caches then)
        config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        hc_config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(service=None),
        )
        hc_config_patcher.start()
        self.addCleanup(hc_config_patcher.stop)

    def test_co_sign_prefill_with_no_config(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": plugin.identifier,
                "identifier": "999993653",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, plugin.requires_auth)

        submission.refresh_from_db()
        self.assertEqual(
            submission.co_sign_data,
            {
                "plugin": plugin.identifier,
                "identifier": "999993653",
                "representation": "",
                "fields": {},
            },
        )
