from unittest import TestCase

import requests_mock
from ape_pie import APIClient

from ..api_clients import pagination_helper


class PaginationTests(TestCase):
    @requests_mock.Mocker()
    def test_only_single_page(self, m):
        client = APIClient("https://example.com")
        m.get(
            requests_mock.ANY,
            json={
                "count": 3,
                "next": None,
                "previous": None,
                "results": [0, 1, 2],
            },
        )

        with client:
            data = client.get("").json()

            all_results = list(pagination_helper(client, data))

        self.assertEqual(len(m.request_history), 1)
        self.assertEqual(all_results, [0, 1, 2])

    @requests_mock.Mocker()
    def test_consume_all_pages(self, m):
        client = APIClient("https://example.com")
        m.get(
            "https://example.com",
            json={
                "count": 3,
                "next": "https://example.com/?page=2",
                "previous": None,
                "results": [0, 1],
            },
        )
        m.get(
            "https://example.com?page=2",
            json={
                "count": 3,
                "next": None,
                "previous": "https://example.com",
                "results": [2],
            },
        )

        with client:
            data = client.get("").json()

            all_results = list(pagination_helper(client, data))

        self.assertEqual(len(m.request_history), 2)
        self.assertEqual(all_results, [0, 1, 2])
