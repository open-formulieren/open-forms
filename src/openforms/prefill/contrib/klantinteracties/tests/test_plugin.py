from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.klantinteracties.models import KlantinteractiesConfig
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ....exceptions import PrefillSkipped
from ..constants import Attributes
from ..plugin import klantinteractiesPlugin


class KlantinteractiesPluginTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self):
        super().setUp()

        config = KlantinteractiesConfig(
            service=ServiceFactory.build(
                api_root="http://localhost:8005/klantinteracties/api/v1/",
                api_type=APITypes.kc,
                header_key="Authorization",
                header_value="Token 9b17346dbb9493f967e6653bbcdb03ac2f7009fa",
                auth_type=AuthTypes.api_key,
            )
        )
        patcher = patch(
            "openforms.contrib.klantinteracties.client.KlantinteractiesConfig.get_solo",
            return_value=config,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_available_attributes(self):
        attributes = klantinteractiesPlugin.get_available_attributes()

        self.assertEqual(attributes, Attributes.choices)

    def test_prefill_values_found(self):
        submission = SubmissionFactory.create(auth_info__value="123456782")
        assert submission.is_authenticated
        plugin = klantinteractiesPlugin

        values = plugin.get_prefill_values(
            submission,
            attributes=[
                Attributes.email,
                Attributes.email_preferred,
                Attributes.phone,
                Attributes.phone_preferred,
            ],
        )

        expected = {
            Attributes.email: [
                "someemail@example.org",
                "devilkiller@example.org",
                "john.smith@gmail.com",
            ],
            Attributes.email_preferred: "john.smith@gmail.com",
            Attributes.phone: ["0687654321", "0612345678"],
            Attributes.phone_preferred: "0612345678",
        }
        self.assertEqual(values, expected)

    def test_prefill_values_not_found(self):
        submission = SubmissionFactory.create(auth_info__value="123456780")
        assert submission.is_authenticated
        plugin = klantinteractiesPlugin

        values = plugin.get_prefill_values(
            submission,
            attributes=[
                Attributes.email,
                Attributes.email_preferred,
                Attributes.phone,
                Attributes.phone_preferred,
            ],
        )

        expected = {
            Attributes.email: [],
            Attributes.email_preferred: None,
            Attributes.phone: [],
            Attributes.phone_preferred: None,
        }
        self.assertEqual(values, expected)

    def test_prefill_values_not_authenticated(self):
        submission = SubmissionFactory.create()
        assert not submission.is_authenticated
        plugin = klantinteractiesPlugin

        with self.assertRaises(PrefillSkipped):
            plugin.get_prefill_values(
                submission,
                attributes=[Attributes.email],
            )
