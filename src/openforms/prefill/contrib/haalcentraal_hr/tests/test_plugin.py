import json
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from requests_mock import Mocker
from zgw_consumers.constants import APITypes
from zgw_consumers.test import mock_service_oas_get

from openforms.authentication.constants import AuthAttribute
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..models import HaalCentraalHRConfig
from ..plugin import HaalCentraalHRPrefill

FILES_DIR = Path(__file__).parent / "files"


class HaalCentraalHRPluginTests(TestCase):
    def test_submission_not_authenticated(self):
        plugin = HaalCentraalHRPrefill("haalcentraal_hr")
        submission = SubmissionFactory.create()

        data = plugin.get_prefill_values(submission, ["address"])

        self.assertEqual(data, {})

    def test_submission_authenticated_with_other_auth_attribute(self):
        plugin = HaalCentraalHRPrefill("haalcentraal_hr")
        submission = SubmissionFactory.create(auth_info__attribute=AuthAttribute.bsn)

        data = plugin.get_prefill_values(submission, ["address"])

        self.assertEqual(data, {})

    @Mocker()
    def test_happy_flow(self, m):
        mock_service_oas_get(
            m,
            url="http://haalcentraal-hr.nl/api/",
            service="haalcentraal-hr-oas",
            oas_url="https://haalcentraal-hr.nl/api/schema/openapi.yaml",
        )

        with open(FILES_DIR / "maatschapplelijkeactiviteiten-response.json", "rb") as f:
            m.get(
                "http://haalcentraal-hr.nl/api/maatschappelijkeactiviteiten/111222333",
                json=json.load(f),
            )

        plugin = HaalCentraalHRPrefill("haalcentraal_hr")
        submission = SubmissionFactory.create(
            auth_info__attribute=AuthAttribute.kvk, auth_info__value="111222333"
        )
        service = ServiceFactory.create(
            api_type=APITypes.orc,
            api_root="http://haalcentraal-hr.nl/api/",
            oas="https://haalcentraal-hr.nl/api/schema/openapi.yaml",
        )

        with patch(
            "openforms.prefill.contrib.haalcentraal_hr.plugin.HaalCentraalHRConfig.get_solo",
            return_value=HaalCentraalHRConfig(service=service),
        ):
            data = plugin.get_prefill_values(
                submission,
                ["kvkNummer", "heeftAlsEigenaar.natuurlijkPersoon.burgerservicenummer"],
            )

        self.assertEqual(data["kvkNummer"], "111222333")
        self.assertEqual(
            data["heeftAlsEigenaar.natuurlijkPersoon.burgerservicenummer"],
            "555555021",
        )
