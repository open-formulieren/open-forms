"""
Unit tests for the Catalogi client.

These tests make use of requests-mock rather than VCR for two reasons:

* the actual API behaviour may not be relevant, rather we're interested in metadata
* we deliberately simulate a broken server implementation and test our robustness for
  those cases. Real implementations should not be broken, so finding a real, broken
  API to run in docker-compose is supposed to be impossible.
"""

from datetime import date

from django.conf import settings
from django.core.cache import caches
from django.test import TestCase, override_settings

import requests_mock
from furl import furl

from openforms.contrib.zgw.clients.catalogi import (
    CaseType,
    Catalogus,
    InformatieObjectType,
)
from openforms.utils.api_clients import PaginatedResponseData
from openforms.utils.tests.cache import clear_caches

from ..clients import CatalogiClient
from ..exceptions import StandardViolation


class CatalogiClientTests(TestCase):
    @requests_mock.Mocker()
    def test_automatic_version_information_extraction(self, m: requests_mock.Mocker):
        client = CatalogiClient(base_url="https://dummy/")
        m.get("https://dummy/", json={}, headers={"API-Version": "1.2.3"})

        with client:
            client.get("")

        self.assertEqual(client.api_version, (1, 2, 3))
        self.assertEqual(len(m.request_history), 1)

    @requests_mock.Mocker()
    def test_version_extraction_from_bad_implementation(self, m: requests_mock.Mocker):
        client = CatalogiClient(base_url="https://dummy/")
        m.register_uri(
            requests_mock.ANY,
            requests_mock.ANY,
            json={},
            headers={"Wrong-Header": "1.2.3"},
        )

        with self.assertRaisesMessage(
            StandardViolation, "API-version is a required response header."
        ):
            client.api_version

    @requests_mock.Mocker()
    def test_version_is_not_semver(self, m: requests_mock.Mocker):
        client = CatalogiClient(base_url="https://dummy/")
        m.register_uri(
            requests_mock.ANY,
            requests_mock.ANY,
            json={},
            headers={"API-version": "latest"},
        )

        with self.assertRaisesMessage(
            StandardViolation, "API-version must follow semver format."
        ):
            client.api_version

    @requests_mock.Mocker()
    def test_returns_too_many_catalogues(self, m: requests_mock.Mocker):
        client = CatalogiClient(base_url="https://dummy/")
        m.get(
            "https://dummy/catalogussen?domein=TEST&rsin=000000000",
            headers={"API-Version": "1.0.0"},
            json={
                "next": None,
                "previous": None,
                "count": 2,
                "results": [
                    {"url": "https://dummy/api/v1/catalogussen/1"},
                    {"url": "https://dummy/api/v1/catalogussen/2"},
                ],
            },
        )
        with self.assertRaisesMessage(
            StandardViolation,
            "Combination of domain + rsin must be unique according to the standard.",
        ):
            client.find_catalogus(domain="TEST", rsin="000000000")

    @requests_mock.Mocker()
    def test_server_does_not_support_filtering_documenttypes_on_valid_date(
        self,
        m: requests_mock.Mocker,
    ):
        client = CatalogiClient(base_url="https://dummy/")
        client._api_version = (1, 0, 0)
        endpoint = furl("https://dummy/informatieobjecttypen").set(
            {
                "catalogus": "https://dummy/catalogus",
                "omschrijving": "Attachment",
            }
        )
        m.get(
            str(endpoint),
            headers={"API-Version": "1.0.0"},
            json={
                "next": None,
                "previous": None,
                "count": 3,
                "results": [
                    {
                        "url": "https://dummy/api/v1/informatieobjecttypen/1",
                        "omschrijving": "Attachment",
                        "beginGeldigheid": "2023-01-01",
                        "eindeGeldigheid": "2023-12-31",
                    },
                    {
                        "url": "https://dummy/api/v1/informatieobjecttypen/2",
                        "omschrijving": "Attachment",
                        "beginGeldigheid": "2024-01-01",
                        "eindeGeldigheid": "2024-12-31",
                    },
                    {
                        "url": "https://dummy/api/v1/informatieobjecttypen/3",
                        "omschrijving": "Attachment",
                        "beginGeldigheid": "2025-01-01",
                        "eindeGeldigheid": None,
                    },
                ],
            },
        )

        results = client.find_informatieobjecttypen(
            catalogus="https://dummy/catalogus",
            description="Attachment",
            valid_on=date(2024, 8, 8),
        )

        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["url"], "https://dummy/api/v1/informatieobjecttypen/2"
        )

    @requests_mock.Mocker()
    def test_server_supports_filtering_document_types_but_doesnt_enforce_unique_versions(
        self, m: requests_mock.Mocker
    ):
        client = CatalogiClient(base_url="https://dummy/")
        client._api_version = (1, 2, 0)
        endpoint = furl("https://dummy/informatieobjecttypen").set(
            {
                "catalogus": "https://dummy/catalogus",
                "omschrijving": "Attachment",
                "datumGeldigheid": "2024-08-08",
            }
        )
        m.get(
            str(endpoint),
            headers={"API-Version": "1.2.0"},
            json={
                "next": None,
                "previous": None,
                "count": 2,
                "results": [
                    {
                        "url": "https://dummy/api/v1/informatieobjecttypen/1",
                        "omschrijving": "Attachment",
                        "beginGeldigheid": "2023-01-01",
                        "eindeGeldigheid": "2024-12-31",
                    },
                    {
                        "url": "https://dummy/api/v1/informatieobjecttypen/2",
                        "omschrijving": "Attachment",
                        "beginGeldigheid": "2024-01-01",
                        "eindeGeldigheid": None,
                    },
                ],
            },
        )

        with self.assertRaisesMessage(
            StandardViolation,
            "Got 2 document type versions within a catalogue with description "
            "'Attachment'. Version (date) ranges may not overlap.",
        ):
            client.find_informatieobjecttypen(
                catalogus="https://dummy/catalogus",
                description="Attachment",
                valid_on=date(2024, 8, 8),
            )

    @requests_mock.Mocker()
    def test_server_does_not_support_filtering_case_types_on_valid_date(
        self,
        m: requests_mock.Mocker,
    ):
        client = CatalogiClient(base_url="https://dummy/")
        client._api_version = (1, 0, 0)
        endpoint = furl("https://dummy/zaaktypen").set(
            {
                "catalogus": "https://dummy/catalogus",
                "identificatie": "ZT-007",
            }
        )
        m.get(
            str(endpoint),
            headers={"API-Version": "1.0.0"},
            json={
                "next": None,
                "previous": None,
                "count": 3,
                "results": [
                    {
                        "url": "https://dummy/api/v1/zaaktypen/1",
                        "identificatie": "ZT-007",
                        "omschrijving": "Zaaktype 007",
                        "beginGeldigheid": "2023-01-01",
                        "eindeGeldigheid": "2023-12-31",
                    },
                    {
                        "url": "https://dummy/api/v1/zaaktypen/2",
                        "identificatie": "ZT-007",
                        "omschrijving": "Zaaktype 7",
                        "beginGeldigheid": "2024-01-01",
                        "eindeGeldigheid": "2024-12-31",
                    },
                    {
                        "url": "https://dummy/api/v1/zaaktypen/3",
                        "identificatie": "ZT-007",
                        "omschrijving": "Zaaktype 7",
                        "beginGeldigheid": "2025-01-01",
                        "eindeGeldigheid": None,
                    },
                ],
            },
        )

        results = client.find_case_types(
            catalogus="https://dummy/catalogus",
            identification="ZT-007",
            valid_on=date(2024, 8, 8),
        )

        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "https://dummy/api/v1/zaaktypen/2")

    @requests_mock.Mocker()
    def test_server_supports_filtering_case_types_but_doesnt_enforce_unique_versions(
        self, m: requests_mock.Mocker
    ):
        client = CatalogiClient(base_url="https://dummy/")
        client._api_version = (1, 2, 0)
        endpoint = furl("https://dummy/zaaktypen").set(
            {
                "catalogus": "https://dummy/catalogus",
                "identificatie": "ZT-007",
                "datumGeldigheid": "2024-08-08",
            }
        )
        m.get(
            str(endpoint),
            headers={"API-Version": "1.2.0"},
            json={
                "next": None,
                "previous": None,
                "count": 2,
                "results": [
                    {
                        "url": "https://dummy/api/v1/zaaktypen/1",
                        "identificatie": "ZT-007",
                        "omschrijving": "Zaaktype 7",
                        "beginGeldigheid": "2023-01-01",
                        "eindeGeldigheid": "2024-12-31",
                    },
                    {
                        "url": "https://dummy/api/v1/zaaktypen/2",
                        "identificatie": "ZT-007",
                        "omschrijving": "Zaaktype 7",
                        "beginGeldigheid": "2024-01-01",
                        "eindeGeldigheid": None,
                    },
                ],
            },
        )

        with self.assertRaisesMessage(
            StandardViolation,
            "Got 2 case type versions within a catalogue with identification "
            "'ZT-007'. Version (date) ranges may not overlap.",
        ):
            client.find_case_types(
                catalogus="https://dummy/catalogus",
                identification="ZT-007",
                valid_on=date(2024, 8, 8),
            )

    @requests_mock.Mocker()
    def test_get_role_types_before_v12(self, m: requests_mock.Mocker):
        client = CatalogiClient(base_url="https://dummy/")
        client._api_version = (1, 0, 0)
        # mocks to get available zaaktypen
        zt_endpoint = furl("https://dummy/zaaktypen").set(
            {
                "catalogus": "https://dummy/catalogus",
                "identificatie": "ZT-007",
            }
        )
        m.get(
            str(zt_endpoint),
            headers={"API-Version": "1.0.0"},
            json={
                "next": None,
                "previous": None,
                "count": 2,
                "results": [
                    {
                        "url": "https://dummy/api/v1/zaaktypen/1",
                        "identificatie": "ZT-007",
                        "beginGeldigheid": "2023-01-01",
                        "eindeGeldigheid": "2023-12-31",
                        "roltypen": [
                            "https://dummy/api/v1/roltypen/1",
                        ],
                    },
                    {
                        "url": "https://dummy/api/v1/zaaktypen/2",
                        "identificatie": "ZT-007",
                        "beginGeldigheid": "2024-01-01",
                        "roltypen": [
                            "https://dummy/api/v1/roltypen/2",
                            "https://dummy/api/v1/roltypen/3",
                        ],
                    },
                ],
            },
        )

        # mocks for two zaaktype versions
        endpoint = furl("https://dummy/roltypen")
        m.get(
            str(endpoint.set({"zaaktype": "https://dummy/api/v1/zaaktypen/1"})),
            headers={"API-Version": "1.0.0"},
            json={
                "next": None,
                "previous": None,
                "count": 1,
                "results": [
                    {
                        "url": "https://dummy/api/v1/roltypen/1",
                        "zaaktype": "https://dummy/api/v1/zaaktypen/1",
                        "omschrijving": "Baliemedewerker",
                        "omschrijvingGeneriek": "klantcontacter",
                    },
                ],
            },
        )
        m.get(
            str(endpoint.set({"zaaktype": "https://dummy/api/v1/zaaktypen/2"})),
            headers={"API-Version": "1.0.0"},
            json={
                "next": None,
                "previous": None,
                "count": 2,
                "results": [
                    {
                        "url": "https://dummy/api/v1/roltypen/2",
                        "zaaktype": "https://dummy/api/v1/zaaktypen/2",
                        "omschrijving": "Baliemedewerker",
                        "omschrijvingGeneriek": "klantcontacter",
                    },
                    {
                        "url": "https://dummy/api/v1/roltypen/3",
                        "zaaktype": "https://dummy/api/v1/zaaktypen/2",
                        "omschrijving": "Behandelaar",
                        "omschrijvingGeneriek": "behandelaar",
                    },
                ],
            },
        )

        results = client.get_all_role_types(
            catalogus="https://dummy/catalogus",
            within_casetype="ZT-007",
        )

        all_results = list(results)
        self.assertEqual(len(all_results), 3)


CACHES = settings.CACHES.copy()
CACHES["catalogi_client"] = {"BACKEND": "openforms.utils.cache.RequestProxyCache"}


@override_settings(CACHES=CACHES)
@requests_mock.Mocker()
class CatalogiClientCachingTests(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.addCleanup(clear_caches)

    def test_version_caching(self, mocker: requests_mock.Mocker):
        client = CatalogiClient(base_url="https://dummy/catalogi/api/v1")
        mocker.get(
            "https://dummy/catalogi/api/v1/catalogussen?domein=VRSN",
            headers={"API-Version": "1.2.3"},
        )

        api_version = client.api_version

        self.assertEqual(api_version, (1, 2, 3))
        self.assertEqual(len(mocker.request_history), 1)

        cache = caches["catalogi_client"]
        cache_key = "ZGW|catalogi|version|https://dummy/catalogi/api/v1"
        self.assertEqual(cache.get(cache_key), (1, 2, 3))

        # Do another request to a random endpoint, not expecting this to increase the
        # mocker's request history but using the cached value instead.
        second_version = client.api_version

        self.assertEqual(second_version, api_version)
        self.assertEqual(len(mocker.request_history), 1)

    def test_catalogi_caching(self, mocker: requests_mock.Mocker):
        client = CatalogiClient(base_url="https://dummy/catalogi/api/v1")

        expected_catalogus: Catalogus = {
            "url": "https://dummy/catalogi/api/v1/catalogussen/7575ec62-a5ed-421f-bfc7-f8837066dd10",
            "domein": "PARTN",
            "rsin": "000000000",
            "naam": "Test partners",
            "informatieobjecttypen": [
                "https://dummy/catalogi/api/v1/informatieobjecttypen/d2ea38b1-5215-402f-a3f5-2977d112bf72"
            ],
            "zaaktypen": [
                "https://dummy/catalogi/api/v1/zaaktypen/77543c85-e5cd-4b3e-b7a5-27165e1334b1"
            ],
        }
        catalogi_response_data: PaginatedResponseData = {
            "count": 1,
            "results": [expected_catalogus],
            "previous": "https://dummy/catalogi/api/v1/catalogussen?page=-1",
            "next": "https://dummy/catalogi/api/v1/catalogussen?page=2",
        }
        mocker.get(
            "https://dummy/catalogi/api/v1/catalogussen",
            json=catalogi_response_data,
            headers={"API-Version": "1.2.3"},
        )

        with client:
            result = client.find_catalogus(domain="PARTN", rsin="000000000")

        self.assertEqual(result, expected_catalogus)
        self.assertEqual(len(mocker.request_history), 1)

        cache = caches["catalogi_client"]
        cache_key = (
            "ZGW|catalogi|find_catalogus|https://dummy/catalogi/api/v1|PARTN|000000000"
        )
        self.assertEqual(cache.get(cache_key), result)

        # Call the find_catalogus method again, not expecting this to increase the
        # mocker's request history but using the cached value instead.
        with client:
            client.find_catalogus(domain="PARTN", rsin="000000000")

        self.assertEqual(len(mocker.request_history), 1)

    def test_case_type_caching(self, mocker: requests_mock.Mocker):
        client = CatalogiClient(base_url="https://dummy/catalogi/api/v1")

        catalogus = "https://dummy/catalogi/api/v1/catalogussen/7575ec62-a5ed-421f-bfc7-f8837066dd10"
        case_types: list[CaseType] = [
            {
                "url": "https://dummy/catalogi/api/v1/zaaktypen/77543c85-e5cd-4b3e-b7a5-27165e1334b1",
                "catalogus": catalogus,
                "identificatie": "ZAAKTYPE-2020-0000000001",
                "omschrijving": "Case type for partners component",
                "beginGeldigheid": "2020-06-20",
                "eindeGeldigheid": None,
                "productenOfDiensten": [],
                "informatieobjecttypen": [
                    "https://dummy/catalogi/api/v1/informatieobjecttypen/d2ea38b1-5215-402f-a3f5-2977d112bf72"
                ],
                "roltypen": [
                    "https://dummy/catalogi/api/v1/roltypen/706464f3-cd55-425c-92ac-76be4ac8a61b",
                    "https://dummy/catalogi/api/v1/roltypen/eedd2d97-19b1-4d66-821b-307f3f44363e",
                ],
            }
        ]
        case_type_response_data: PaginatedResponseData[CaseType] = {
            "count": 1,
            "results": case_types,
            "previous": "",
            "next": "",
        }

        mocker.get(
            f"https://dummy/catalogi/api/v1/zaaktypen?catalogus={catalogus}",
            json=case_type_response_data,
            headers={"API-Version": "1.2.3"},
        )
        # the client will do an API version check to determine if filtering
        # on the `valid_on` query parameter is supported
        mocker.get(
            "https://dummy/catalogi/api/v1/catalogussen?domein=VRSN",
            json={},
            headers={"API-Version": "1.2.3"},
        )

        with client:
            results = client.find_case_types(
                catalogus=catalogus,
                identification="",
            )
            assert results is not None

        self.assertEqual(results, case_types)
        self.assertEqual(len(mocker.request_history), 2)

        cache = caches["catalogi_client"]
        cache_key = (
            f"ZGW|catalogi|find_case_types|https://dummy/catalogi/api/v1|{catalogus}|"
        )
        self.assertEqual(cache.get(cache_key), case_types)

        # Call the find_case_types method again, not expecting this to increase the
        # mocker's request history but using the cached value instead.
        with client:
            results = client.find_case_types(
                catalogus=catalogus,
                identification="",
            )
            assert results is not None

        self.assertEqual(len(mocker.request_history), 2)

    def test_informatieobjecttype_caching(self, mocker: requests_mock.Mocker):
        client = CatalogiClient(base_url="https://dummy/catalogi/api/v1")

        catalogus = "https://dummy/catalogi/api/v1/catalogussen/7575ec62-a5ed-421f-bfc7-f8837066dd10"
        informatieobjecttypen: list[InformatieObjectType] = [
            {
                "url": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/d2ea38b1-5215-402f-a3f5-2977d112bf72",
                "catalogus": "http://localhost:8003/catalogi/api/v1/catalogussen/7575ec62-a5ed-421f-bfc7-f8837066dd10",
                "omschrijving": "Partners PDF Informatieobjecttype",
                "beginGeldigheid": "2020-06-20",
                "eindeGeldigheid": None,
            }
        ]
        informatieobjecttypen_response_data: PaginatedResponseData[
            InformatieObjectType
        ] = {
            "count": 1,
            "results": informatieobjecttypen,
            "previous": "",
            "next": "",
        }

        mocker.get(
            f"https://dummy/catalogi/api/v1/informatieobjecttypen?catalogus={catalogus}&omschrijving=",
            json=informatieobjecttypen_response_data,
            headers={"API-Version": "1.2.3"},
        )
        # the client will do an API version check to determine if filtering
        # on the `valid_on` query parameter is supported
        mocker.get(
            "https://dummy/catalogi/api/v1/catalogussen?domein=VRSN",
            json={},
            headers={"API-Version": "1.2.3"},
        )

        with client:
            results = client.find_informatieobjecttypen(
                catalogus=catalogus,
                description="",
            )
            assert results is not None

        self.assertEqual(results, informatieobjecttypen)
        self.assertEqual(len(mocker.request_history), 2)

        cache = caches["catalogi_client"]
        cache_key = f"ZGW|catalogi|find_informatieobjecttypen|https://dummy/catalogi/api/v1|{catalogus}|"
        self.assertEqual(cache.get(cache_key), informatieobjecttypen)

        # Call the find_case_types method again, not expecting this to increase the
        # mocker's request history but using the cached value instead.
        with client:
            results = client.find_informatieobjecttypen(
                catalogus=catalogus,
                description="",
            )
            assert results is not None

        self.assertEqual(len(mocker.request_history), 2)
