from functools import partial

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings
from django.utils.translation import gettext as _

import requests_mock
from freezegun import freeze_time
from privates.test import temp_private_root

from openforms.submissions.models import Submission
from openforms.tests.utils import NOOP_CACHES
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin

from ..validators import (
    KVKBranchNumberRemoteValidator,
    KVKNumberRemoteValidator,
    KVKRSINRemoteValidator,
    validate_branchNumber,
    validate_kvk,
)
from .base import KVKTestMixin


class KvKValidatorTestCase(SimpleTestCase):
    @staticmethod
    def test_valid_kvks():
        validate_kvk("12345678")

    def test_invalid_kvks(self):
        with self.assertRaises(ValidationError):
            validate_kvk("1234567890")

        with self.assertRaises(ValidationError):
            validate_kvk("1234567a")

        with self.assertRaises(ValidationError):
            validate_kvk("1234-567")

    @staticmethod
    def test_valid_branchNumber():
        validate_branchNumber("112233445566")

    def test_invalid_branchNumber(self):
        with self.assertRaises(ValidationError):
            validate_branchNumber("1122334455")

        with self.assertRaises(ValidationError):
            validate_branchNumber("11223344556a")

        with self.assertRaises(ValidationError):
            validate_branchNumber("11223-445566")


@override_settings(CACHES=NOOP_CACHES)
@temp_private_root()
class KvKRemoteValidatorTestCase(OFVCRMixin, KVKTestMixin, SimpleTestCase):
    def test_kvkNumber_validator(self):
        # valid-existing kvkNummer
        validator = partial(KVKNumberRemoteValidator("id"), submission=Submission())
        validator("69599084")

        # invalid kvkNummer(404)
        with self.assertRaisesMessage(
            ValidationError, _("%(type)s does not exist.") % {"type": _("KvK number")}
        ):
            validator("90004333")

        with self.assertRaisesMessage(
            ValidationError,
            _("%(type)s should have %(size)i characters.")
            % {"type": _("KvK number"), "size": 8},
        ):
            validator("123")
        with self.assertRaisesMessage(
            ValidationError, _("Expected a numerical value.")
        ):
            validator("bork")

    def test_rsin_validator(self):
        validator = partial(KVKRSINRemoteValidator("id"), submission=Submission())

        # valid rsin
        validator("992760562")

        # invalid rsin(404)
        with self.assertRaisesMessage(
            ValidationError, _("%(type)s does not exist.") % {"type": _("RSIN")}
        ):
            validator("123456782")

        with self.assertRaisesMessage(
            ValidationError,
            _("%(type)s should have %(size)i characters.")
            % {"type": _("RSIN"), "size": 9},
        ):
            validator("123")
        with self.assertRaisesMessage(
            ValidationError, _("Expected a numerical value.")
        ):
            validator("bork")

    def test_branchNumber_validator(self):
        validator = partial(KVKBranchNumberRemoteValidator(""), submission=Submission())
        validator("990000541921")

        with self.assertRaisesMessage(
            ValidationError,
            _("%(type)s does not exist.") % {"type": _("Branch number")},
        ):
            validator("665544332211")

        with self.assertRaisesMessage(
            ValidationError,
            _("%(type)s should have %(size)i characters.")
            % {"type": _("Branch number"), "size": 12},
        ):
            validator("123")
        with self.assertRaisesMessage(
            ValidationError, _("Expected a numerical value.")
        ):
            validator("bork")


class KvKRemoteValidatorCachingTestCase(KVKTestMixin, SimpleTestCase):
    # Rather than using VCR, we use requests mock because we don't check the contents
    # of the responses (they are not relevant for the behaviour being tested).
    # So, instead we use requests-mock and check the amount of calls made.

    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)
        clear_caches()

        self.mocker = requests_mock.Mocker()
        self.addCleanup(self.mocker.stop)
        self.mocker.start()
        self.mocker.get(requests_mock.ANY, json={"resultaten": ["MOCK"]})

    def assertNumRequests(self, expected: int):
        num_requests = len(self.mocker.request_history)
        self.assertEqual(
            num_requests,
            expected,
            f"Expected {expected} requests, got {num_requests} instead.",
        )

    def test_kvkNumber_validator_caching(self):
        # valid-existing kvkNummer
        validator = partial(KVKNumberRemoteValidator("id"), submission=Submission())

        with freeze_time("2024-01-01T12:00:00"):
            self.assertNumRequests(0)

            validator("69599084")

            self.assertNumRequests(1)

            validator("69599084")

            # No additional request has been made because the result was cached
            self.assertNumRequests(1)

            validator("68727720")

            # validate with different KVK number should trigger new request
            self.assertNumRequests(2)

        with freeze_time("2024-01-01T12:05:01"):
            validator("69599084")

        # Request is made, because cached result is timed out
        self.assertNumRequests(3)

    def test_rsin_validator_caching(self):
        validator = partial(KVKRSINRemoteValidator("id"), submission=Submission())

        with freeze_time("2024-01-01T12:00:00"):
            self.assertNumRequests(0)

            validator("992760562")

            self.assertNumRequests(1)

            validator("992760562")

            # No additional request has been made because the result was cached
            self.assertNumRequests(1)

            validator("858311537")

            # validate with different RSIN should trigger new request
            self.assertNumRequests(2)

        with freeze_time("2024-01-01T12:05:01"):
            validator("992760562")

        # Request is made, because cached result is timed out
        self.assertNumRequests(3)

    def test_branchNumber_validator_caching(self):
        validator = partial(KVKBranchNumberRemoteValidator(""), submission=Submission())

        with freeze_time("2024-01-01T12:00:00"):
            self.assertNumRequests(0)

            validator("990000541921")

            self.assertNumRequests(1)

            validator("990000541921")

            # No additional request has been made because the result was cached
            self.assertNumRequests(1)

            validator("990000216645")

            # validate with different branchnumber should trigger new request
            self.assertNumRequests(2)

        with freeze_time("2024-01-01T12:05:01"):
            validator("990000541921")

        # Request is made, because cached result is timed out
        self.assertNumRequests(3)
