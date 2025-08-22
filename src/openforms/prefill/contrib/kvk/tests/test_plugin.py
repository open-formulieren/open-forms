from django.test import TestCase

import requests_mock
from privates.test import temp_private_root

from openforms.authentication.service import AuthAttribute
from openforms.authentication.tests.factories import AuthInfoFactory
from openforms.contrib.kvk.tests.base import KVKTestMixin, load_json_mock
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import Attributes
from ..plugin import KVK_KVKNumberPrefill


@temp_private_root()
class KVKPrefillTests(KVKTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_get_prefill_values(self, m):
        m.get(
            f"{self.api_root}v1/basisprofielen/69599084",
            status_code=200,
            json=load_json_mock("basisprofiel_response.json"),
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")

        submission = SubmissionFactory.create(
            auth_info__value="69599084",
            auth_info__plugin="kvk",
            auth_info__attribute=AuthAttribute.kvk,
        )
        values = plugin.get_prefill_values(
            submission,
            [
                Attributes.bezoekadres_straatnaam,
                Attributes.kvkNummer,
                "invalidAttribute",
            ],
        )
        expected = {
            "bezoekadres.straatnaam": "Abebe Bikilalaan",
            "kvkNummer": "69599084",
        }
        self.assertEqual(values, expected)

    def test_get_prefill_values_not_authenticated(self):
        plugin = KVK_KVKNumberPrefill(identifier="kvk")

        submission = SubmissionFactory.create()
        assert not submission.is_authenticated

        values = plugin.get_prefill_values(
            submission,
            [Attributes.bezoekadres_straatnaam, Attributes.kvkNummer],
        )
        expected = {}
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_vve(self, m):
        m.get(
            f"{self.api_root}v1/basisprofielen/90000749",
            status_code=200,
            json=load_json_mock("basisprofiel_response_vve.json"),
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        submission = SubmissionFactory.create(
            auth_info__value="90000749",
            auth_info__plugin="kvk",
            auth_info__attribute=AuthAttribute.kvk,
        )
        values = plugin.get_prefill_values(
            submission,
            [Attributes.bezoekadres_straatnaam, Attributes.kvkNummer],
        )
        expected = {
            "bezoekadres.straatnaam": "Blaauwweg",
            "kvkNummer": "90000749",
        }
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_404(self, m):
        m.get(
            f"{self.api_root}v1/basisprofielen/69599084",
            status_code=404,
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        auth_info = AuthInfoFactory.create(
            value="69599084", plugin="kvk", attribute=AuthAttribute.kvk
        )
        submission = SubmissionFactory.create(auth_info=auth_info)
        values = plugin.get_prefill_values(
            submission,
            [Attributes.bezoekadres_straatnaam, Attributes.kvkNummer],
        )
        expected = {}
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_500(self, m):
        m.get(
            f"{self.api_root}v1/basisprofielen/69599084",
            status_code=500,
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        auth_info = AuthInfoFactory.create(
            value="69599084", plugin="kvk", attribute=AuthAttribute.kvk
        )
        submission = SubmissionFactory.create(auth_info=auth_info)
        values = plugin.get_prefill_values(
            submission,
            [Attributes.bezoekadres_straatnaam, Attributes.kvkNummer],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_available_attributes(self):
        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        attrs = plugin.get_available_attributes()
        self.assertIsInstance(attrs, list)
        self.assertIsInstance(attrs[0], tuple)  # pyright: ignore[reportIndexIssue]
        self.assertEqual(len(attrs[0]), 2)  # pyright: ignore[reportIndexIssue]

    def test_plugin_usage_without_configuring_kvk_service(self):
        config = self.config_mock.return_value
        # remove KVK service configuration
        config.search_service = None
        config.profile_service = None
        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        submission = SubmissionFactory.create(
            auth_info__value="69599084",
            auth_info__plugin="kvk",
            auth_info__attribute=AuthAttribute.kvk,
        )

        values = plugin.get_prefill_values(
            submission,
            [Attributes.bezoekadres_straatnaam, Attributes.kvkNummer],
        )

        self.assertEqual(values, {})
