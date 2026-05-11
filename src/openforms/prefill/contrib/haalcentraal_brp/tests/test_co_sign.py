from unittest.mock import patch

from django.test import TestCase

from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ....co_sign import add_co_sign_representation
from ....models import PrefillConfig
from ....registry import register
from ..plugin import PLUGIN_IDENTIFIER

plugin = register[PLUGIN_IDENTIFIER]

AUTH_ATTRIBUTE = next(attr for attr in plugin.requires_auth)


class CoSignPrefillTests(OFVCRMixin, TestCase):
    def setUp(self):
        super().setUp()

        api_root = "http://localhost:5010/haalcentraal/api/brp/"
        # mock out django-solo interface (we don't have to deal with caches then)
        co_sign_config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        co_sign_config_patcher.start()
        self.addCleanup(co_sign_config_patcher.stop)

        # set up patcher for the configuration
        hc_config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root=api_root,
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        )
        hc_config_patcher = patch(
            "openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo",
            return_value=hc_config,
        )
        hc_config_patcher.start()
        self.addCleanup(hc_config_patcher.stop)

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
            "representation": "C.F. Wiegman",
            "fields": {
                "naam.voornamen": "Cornelia Francisca",
                "naam.voorletters": "C.F.",
                "naam.geslachtsnaam": "Wiegman",
            },
        }
        self.assertEqual(submission.co_sign_data, expected)

    def test_incomplete_data_returned(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "version": "v1",
                "plugin": plugin.identifier,
                "identifier": "000009922",
                "co_sign_auth_attribute": "bsn",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, AUTH_ATTRIBUTE)

        submission.refresh_from_db()
        expected = {
            "version": "v1",
            "plugin": plugin.identifier,
            "identifier": "000009922",
            "representation": "",
            "co_sign_auth_attribute": "bsn",
            "fields": {},
        }
        self.assertEqual(submission.co_sign_data, expected)


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
        self.addCleanup(config_patcher.stop)

        co_sign_config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        co_sign_config_patcher.start()
        self.addCleanup(co_sign_config_patcher.stop)

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
