from unittest.mock import patch

from django.test import override_settings

import requests
import requests_mock
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.test.factories import ServiceFactory

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
            "https://kadaster/v3_1/free",
            status_code=200,
            json={
                "response": {
                    "numFound": 1,
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
            },
        )

        url = reverse("api:geo:address-search")
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
        url = reverse("api:geo:address-search")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_call_with_no_query_parameter(self):
        url = reverse("api:geo:address-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["invalidParams"]

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["code"], "required")
        self.assertEqual(errors[0]["name"], "q")

    @requests_mock.Mocker()
    def test_call_with_api_get_bag_response_exception(self, m):
        m.get(
            "https://kadaster/v3_1/free",
            exc=requests.RequestException,
        )
        url = reverse("api:geo:address-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body, [])

    @requests_mock.Mocker()
    def test_call_with_api_return_something_other_then_200(self, m):
        m.get(
            "https://kadaster/v3_1/free",
            status_code=400,
            json={
                "error": {
                    "code": 400,
                    "metadata": ["error-class"],
                    "msg": "undefined field",
                }
            },
        )

        url = reverse("api:geo:address-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body, [])

    @requests_mock.Mocker()
    def test_call_with_api_return_data_not_having_response(self, m):
        m.get("https://kadaster/v3_1/free", status_code=200, json={})

        url = reverse("api:geo:address-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body, [])

    @requests_mock.Mocker()
    def test_call_with_api_return_data_not_having_docs(self, m):
        m.get(
            "https://kadaster/v3_1/free",
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

        url = reverse("api:geo:address-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body, [])

    @requests_mock.Mocker()
    def test_call_with_api_return_data_not_having_centroide_ll(self, m):
        m.get(
            "https://kadaster/v3_1/free",
            status_code=200,
            json={
                "response": {
                    "numFound": 1,
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
            },
        )

        url = reverse("api:geo:address-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body, [])

    @requests_mock.Mocker()
    def test_call_with_api_return_data_not_having_centroide_rd(self, m):
        m.get(
            "https://kadaster/v3_1/free",
            status_code=200,
            json={
                "response": {
                    "numFound": 1,
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
                },
            },
        )

        url = reverse("api:geo:address-search")
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
                    "rd": None,
                },
            ],
        )

    @requests_mock.Mocker()
    def test_malformed_coordinates(self, m):
        # Hypothetical response where the geometry is not a two-tuple point.
        m.get(
            "https://kadaster/v3_1/free",
            status_code=200,
            json={
                "response": {
                    "numFound": 1,
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
                            # added a Z coordinate which would crash parsing
                            "centroide_ll": "POINT(5.0747543 52.09113798 1)",
                            "gemeentecode": "0344",
                            "weergavenaam": "Gemeente Utrecht",
                            "provincieafkorting": "UT",
                            # added a Z coordinate which would crash parsing
                            "centroide_rd": "POINT(133587.182 455921.594 1)",
                            "id": "gem-df0ca8ab37eccea5217e2a13f74d2833",
                            "gemeentenaam": "Utrecht",
                            "score": 9.7794895,
                        },
                    ],
                }
            },
        )

        url = reverse("api:geo:address-search")
        self._add_submission_to_session(self.submission)

        response = self.client.get(url, {"q": "utrecht"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body, [])
