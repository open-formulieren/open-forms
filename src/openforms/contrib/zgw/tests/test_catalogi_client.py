"""
Unit tests for the Catalogi client.

These tests make use of requests-mock rather than VCR for two reasons:

* the actual API behaviour may not be relevant, rather we're interested in metadata
* we deliberately simulate a broken server implementation and test our robustness for
  those cases. Real implementations should not be broken, so finding a real, broken
  API to run in docker-compose is supposed to be impossible.
"""

from datetime import date

from django.test import TestCase

import requests_mock
from furl import furl

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
