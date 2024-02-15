from functools import partial

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from privates.test import temp_private_root

from openforms.submissions.models import Submission
from openforms.utils.tests.vcr import OFVCRMixin

from ..validators import (
    KVKBranchNumberRemoteValidator,
    KVKNumberRemoteValidator,
    KVKRSINRemoteValidator,
    validate_branchNumber,
    validate_kvk,
)
from .base import TEST_FILES, KVKTestMixin


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


@temp_private_root()
class KvKRemoteValidatorTestCase(OFVCRMixin, KVKTestMixin, SimpleTestCase):
    VCR_TEST_FILES = TEST_FILES

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
        # kvk test environment does not provide an example of valid rsin numbers so we
        # only test against the invalid one
        # https://developers.kvk.nl/documentation/testing

        validator = partial(KVKRSINRemoteValidator("id"), submission=Submission())

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
