from unittest.mock import patch

from django.test import override_settings

import requests
import requests_mock
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.appointments.contrib.qmatic.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..models import KadasterApiConfig


@override_settings(LANGUAGE_CODE="en")
class AddressSearchApiTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = SubmissionFactory.create()

        cls.kadaster_service = ServiceFactory.build(
            api_root="https://kadaster/",
        )

    def setUp(self):
        super().setUp()

        self.config = KadasterApiConfig(search_service=self.kadaster_service)
        config_patcher = patch(
            "openforms.contrib.kadaster.clients.KadasterApiConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    @requests_mock.Mocker()
    def test_call_with_query_parameter_utrecht(self, m):
        m.get(
            "https://kadaster/v3_1/reverse",
            status_code=200,
            json={
                "response": {
                    "numFound": 1,
                    "start": 0,
                    "maxScore": 7.2816563,
                    "numFoundExact": True,
                    "docs": [
                        {
                            "type": "adres",
                            "weergavenaam": "Gemeente Utrecht",
                            "id": "adr-eebf5ada9e3af187be3704b2b01d4dec",
                            "score": 7.2816563,
                            "afstand": 7307439.14,
                        },
                    ],
                }
            },
        )

        url = reverse("api:geo:latlng-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"lat": "52.09113798", "lng": "5.0747543"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(
            body,
            {
                "label": "Gemeente Utrecht",
            },
        )

    def test_call_with_no_active_submission(self):
        url = reverse("api:geo:latlng-search")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_call_with_no_query_parameter(self):
        url = reverse("api:geo:latlng-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["invalidParams"]

        self.assertEqual(len(errors), 2)
        codes = {error["code"] for error in errors}
        self.assertEqual(codes, {"required"})
        names = {error["name"] for error in errors}
        self.assertEqual(names, {"lat", "lng"})

    def test_call_with_no_lat_parameter(self):
        url = reverse("api:geo:latlng-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"lng": "5.0747543"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["invalidParams"]

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["code"], "required")
        self.assertEqual(errors[0]["name"], "lat")

    def test_call_with_no_lng_parameter(self):
        url = reverse("api:geo:latlng-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"lat": "52.09113798"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["invalidParams"]

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["code"], "required")
        self.assertEqual(errors[0]["name"], "lng")

    @requests_mock.Mocker()
    def test_call_with_api_get_bag_response_exception(self, m):
        m.get(
            "https://kadaster/v3_1/reverse",
            exc=requests.RequestException,
        )
        url = reverse("api:geo:latlng-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"lat": "52.09113798", "lng": "5.0747543"})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @requests_mock.Mocker()
    def test_call_with_api_return_something_other_then_200(self, m):
        m.get(
            "https://kadaster/v3_1/reverse",
            status_code=400,
            json={
                "error": {
                    "code": 400,
                    "metadata": ["error-class"],
                    "msg": "undefined field",
                }
            },
        )

        url = reverse("api:geo:latlng-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"lat": "52.09113798", "lng": "5.0747543"})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @requests_mock.Mocker()
    def test_call_with_api_return_data_not_having_response(self, m):
        m.get("https://kadaster/v3_1/reverse", status_code=200, json={})

        url = reverse("api:geo:latlng-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"lat": "52.09113798", "lng": "5.0747543"})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @requests_mock.Mocker()
    def test_call_with_api_return_data_not_having_docs(self, m):
        m.get(
            "https://kadaster/v3_1/reverse",
            status_code=200,
            json={
                "response": {
                    "numFound": 0,
                    "start": 0,
                    "maxScore": None,
                    "numFoundExact": False,
                }
            },
        )

        url = reverse("api:geo:latlng-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"lat": "52.09113798", "lng": "5.0747543"})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @requests_mock.Mocker()
    def test_call_with_api_return_data_not_having_weergavenaam(self, m):
        m.get(
            "https://kadaster/v3_1/reverse",
            status_code=200,
            json={
                "response": {
                    "numFound": 1,
                    "start": 0,
                    "maxScore": 7.2816563,
                    "numFoundExact": True,
                    "docs": [
                        {
                            "type": "adres",
                            "id": "adr-eebf5ada9e3af187be3704b2b01d4dec",
                            "score": 7.2816563,
                            "afstand": 7307439.14,
                        },
                    ],
                }
            },
        )

        url = reverse("api:geo:latlng-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"lat": "52.09113798", "lng": "5.0747543"})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
