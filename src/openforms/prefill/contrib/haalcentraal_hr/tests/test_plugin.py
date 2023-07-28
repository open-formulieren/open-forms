import json
import os
from pathlib import Path
from unittest.mock import patch
from zgw_consumers.test import mock_service_oas_get

from django.test import TestCase

from requests_mock import Mocker

from openforms.authentication.constants import AuthAttribute
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory
from soap.tests.factories import SoapServiceFactory

from ...haalcentraal.tests.utils import load_binary_mock
from ..models import HaalCentraalHRConfig
from ..plugin import HaalCentraalHRPrefill


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
    def test_error_while_getting_saml_token(self, m):
        plugin = HaalCentraalHRPrefill("haalcentraal_hr")
        submission = SubmissionFactory.create(
            auth_info__attribute=AuthAttribute.kvk, auth_info__value="111111111"
        )

        mock_service_oas_get(m, "http://haalcentraal-hr.nl/haalcentraal/api/hr", oas_url="http://haalcentraal-hr.nl/api/oas", service="haalcentraal-hr-oas")
        path_response = Path(__file__).parent / "files" / "maatschapplelijkeactiviteiten-response.json"
        m.get("http://haalcentraal-hr.nl/haalcentraal/api/hr/maatschappelijkeactiviteiten/111111111", json=json.loads(path_response.read_bytes()))

        with patch(
            "openforms.prefill.contrib.haalcentraal_hr.plugin.HaalCentraalHRConfig.get_solo",
            return_value=HaalCentraalHRConfig(
                token_service=SoapServiceFactory.create(
                    url="http://token-service.nl/tokenservice",
                ),
                service=ServiceFactory.create(api_root="http://haalcentraal-hr.nl/haalcentraal/api/hr", oas="http://haalcentraal-hr.nl/api/oas")
            ),
        ), patch(
            "openforms.prefill.contrib.haalcentraal_hr.plugin.HaalCentraalHRPrefill.get_saml_token",
            return_value="the-magic-token",
        ):  # TODO fix when you get WSDL
            data = plugin.get_prefill_values(submission, ["heeftAlsEigenaar.natuurlijkPersoon.burgerservicenummer"])

        self.assertEqual(data, {"heeftAlsEigenaar.natuurlijkPersoon.burgerservicenummer": "555555021"})
