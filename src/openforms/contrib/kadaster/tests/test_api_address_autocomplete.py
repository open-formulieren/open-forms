from unittest.mock import patch

from django.conf import settings
from django.core.cache import caches
from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from zgw_consumers.test.factories import ServiceFactory

from openforms.formio.components.utils import salt_location_message
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..clients.bag import AddressResult
from ..models import KadasterApiConfig

CACHES = settings.CACHES.copy()
CACHES["default"] = {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}


@override_settings(CACHES=CACHES)
class GetStreetNameAndCityViewAPITests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = SubmissionFactory.create()

    def setUp(self):
        super().setUp()
        caches["default"].clear()
        self.addCleanup(caches["default"].clear)
        self._add_submission_to_session(self.submission)

    @patch("openforms.contrib.kadaster.api.views.lookup_address")
    def test_getting_street_name_and_city(self, m_lookup_address):
        m_lookup_address.return_value = AddressResult(
            street_name="Keizersgracht", city="Amsterdam", secret_street_city=""
        )

        response = self.client.get(
            reverse("api:geo:address-autocomplete"),
            {"postcode": "1015CJ", "house_number": "117"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        self.assertEqual(response.json()["streetName"], "Keizersgracht")
        self.assertEqual(response.json()["city"], "Amsterdam")
        self.assertEqual(response.json()["secretStreetCity"], "")

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_getting_street_name_and_city_without_post_code_returns_error(self, _mock):
        response = self.client.get(
            reverse("api:geo:address-autocomplete"),
            {"house_number": "117"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "postcode",
                        "code": "required",
                        "reason": _("This field is required."),
                    }
                ],
            },
        )

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_getting_street_name_and_city_without_house_number_returns_error(
        self, _mock
    ):
        response = self.client.get(
            reverse("api:geo:address-autocomplete"),
            {"postcode": "1015CJ"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "houseNumber",
                        "code": "required",
                        "reason": _("This field is required."),
                    }
                ],
            },
        )

    @patch("openforms.contrib.kadaster.api.views.lookup_address")
    def test_getting_street_name_and_city_with_extra_query_params_ignores_extra_param(
        self, m_lookup_address
    ):
        m_lookup_address.return_value = AddressResult(
            street_name="Keizersgracht", city="Amsterdam", secret_street_city=""
        )

        response = self.client.get(
            reverse("api:geo:address-autocomplete"),
            {"postcode": "1015CJ", "house_number": "117", "random": "param"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        self.assertEqual(response.json()["streetName"], "Keizersgracht")
        self.assertEqual(response.json()["city"], "Amsterdam")
        self.assertEqual(response.json()["secretStreetCity"], "")

    @patch("openforms.contrib.kadaster.api.views.lookup_address")
    def test_address_not_found_returns_empty_strs_200_response(self, m_lookup_address):
        m_lookup_address.return_value = AddressResult(
            street_name="", city="", secret_street_city=""
        )

        response = self.client.get(
            reverse("api:geo:address-autocomplete"),
            {"postcode": "1015CJ", "house_number": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"streetName": "", "city": "", "secretStreetCity": ""}
        )

    @tag("gh-1832")
    @patch("openforms.contrib.kadaster.api.views.lookup_address")
    def test_endpoint_uses_caching(self, m_lookup_address):
        m_lookup_address.return_value = AddressResult(
            street_name="Keizersgracht", city="Amsterdam", secret_street_city=""
        )
        endpoint = reverse("api:geo:address-autocomplete")

        # make the request twice, second one should use cache
        self.client.get(endpoint, {"postcode": "1015CJ", "house_number": "117"})
        self.client.get(endpoint, {"postcode": "1015CJ", "house_number": "117"})

        # assert that the client call was only made once
        m_lookup_address.assert_called_once_with("1015CJ", "117")

    @patch("openforms.contrib.kadaster.clients.KadasterApiConfig.get_solo")
    def test_bag_config_client_used(self, m_get_solo):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)
        m_get_solo.return_value = KadasterApiConfig(
            bag_service=ServiceFactory.build(
                api_root="https://bag/api/",
            )
        )
        endpoint = reverse("api:geo:address-autocomplete")

        with requests_mock.Mocker() as m:
            m.get(
                "https://bag/api/adressen?huisnummer=117&postcode=1015CJ", json={}
            )  # pretend there are no results

            response = self.client.get(
                endpoint, {"postcode": "1015CJ", "house_number": "117"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "streetName": "",
                "city": "",
                "secretStreetCity": salt_location_message(
                    {
                        "postcode": "1015CJ",
                        "number": "117",
                        "city": "",
                        "street_name": "",
                    }
                ),
            },
        )
