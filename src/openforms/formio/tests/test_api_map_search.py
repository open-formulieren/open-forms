from unittest.mock import MagicMock, patch

from django.test import override_settings

import requests
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin


@override_settings(LANGUAGE_CODE="en")
class MapSearchApiTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()

    def tearDown(self):
        self._clear_session()

    @patch("openforms.formio.api.views.requests")
    def test_call_with_query_parameter_utrecht(self, mock_requests):
        # mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {
                "numFound": 205959,
                "start": 0,
                "maxScore": 9.7794895,
                "numFoundExact": True,
                "docs": [
                    {
                        "bron": "Bestuurlijke Grenzen",
                        "identificatie": "0344",
                        "provinciecode": "PV26",
                        "type": "gemeente",
                        "provincienaam": "Utrecht",
                        "centroide_ll": "POINT(5.0747543 52.09113798)",
                        "gemeentecode": "0344",
                        "weergavenaam": "Gemeente Utrecht",
                        "provincieafkorting": "UT",
                        "centroide_rd": "POINT(133587.182 455921.594)",
                        "id": "gem-df0ca8ab37eccea5217e2a13f74d2833",
                        "gemeentenaam": "Utrecht",
                        "score": 9.7794895,
                    },
                ],
            }
        }

        mock_requests.get.return_value = mock_response
        url = reverse("api:formio:map-search")

        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(
            body,
            [
                {
                    "label": "Gemeente Utrecht",
                    "latLng": {"lat": 52.09113798, "lng": 5.0747543},
                    "rd": {"x": 133587.182, "y": 455921.594},
                },
            ],
        )

    def test_call_with_no_active_submission(self):
        url = reverse("api:formio:map-search")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_call_with_no_query_parameter(self):
        url = reverse("api:formio:map-search")

        self._add_submission_to_session(self.submission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("openforms.formio.api.views.requests")
    def test_call_with_api_get_bag_data_exception(self, mock_requests):
        mock_requests.side_effect = requests.exceptions.RequestException
        url = reverse("api:formio:map-search")

        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body, [])

    @patch("openforms.formio.api.views.requests")
    def test_call_with_api_return_something_other_then_200(self, mock_requests):
        # mock the response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "code": 400,
                "metadata": ["error-class"],
                "msg": "undefined field",
            }
        }

        mock_requests.get.return_value = mock_response
        url = reverse("api:formio:map-search")

        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body, [])

    @patch("openforms.formio.api.views.requests")
    def test_call_with_api_return_data_not_having_response(self, mock_requests):
        # mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_requests.get.return_value = mock_response
        url = reverse("api:formio:map-search")

        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body, [])

    @patch("openforms.formio.api.views.requests")
    def test_call_with_api_return_data_not_having_docs(self, mock_requests):
        # mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {
                "numFound": 205959,
                "start": 0,
                "maxScore": 9.7794895,
                "numFoundExact": True,
            }
        }

        mock_requests.get.return_value = mock_response
        url = reverse("api:formio:map-search")

        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body, [])

    @patch("openforms.formio.api.views.requests")
    def test_call_with_api_return_data_not_having_centroide_ll(self, mock_requests):
        # mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {
                "numFound": 205959,
                "start": 0,
                "maxScore": 9.7794895,
                "numFoundExact": True,
                "docs": [
                    {
                        "bron": "Bestuurlijke Grenzen",
                        "identificatie": "0344",
                        "provinciecode": "PV26",
                        "type": "gemeente",
                        "provincienaam": "Utrecht",
                        "gemeentecode": "0344",
                        "weergavenaam": "Gemeente Utrecht",
                        "provincieafkorting": "UT",
                        "centroide_rd": "POINT(133587.182 455921.594)",
                        "id": "gem-df0ca8ab37eccea5217e2a13f74d2833",
                        "gemeentenaam": "Utrecht",
                        "score": 9.7794895,
                    },
                ],
            }
        }

        mock_requests.get.return_value = mock_response
        url = reverse("api:formio:map-search")

        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body, [])

    @patch("openforms.formio.api.views.requests")
    def test_call_with_api_return_data_not_having_centroide_rd(self, mock_requests):
        # mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {
                "numFound": 205959,
                "start": 0,
                "maxScore": 9.7794895,
                "numFoundExact": True,
                "docs": [
                    {
                        "bron": "Bestuurlijke Grenzen",
                        "identificatie": "0344",
                        "provinciecode": "PV26",
                        "type": "gemeente",
                        "provincienaam": "Utrecht",
                        "centroide_ll": "POINT(5.0747543 52.09113798)",
                        "gemeentecode": "0344",
                        "weergavenaam": "Gemeente Utrecht",
                        "provincieafkorting": "UT",
                        "id": "gem-df0ca8ab37eccea5217e2a13f74d2833",
                        "gemeentenaam": "Utrecht",
                        "score": 9.7794895,
                    },
                ],
            }
        }

        mock_requests.get.return_value = mock_response
        url = reverse("api:formio:map-search")

        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body, [])
