from functools import partial

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.utils.translation import gettext as _

import requests_mock
from privates.test import temp_private_root

from ..validators import (
    KVKBranchNumberRemoteValidator,
    KVKNumberRemoteValidator,
    KVKRSINRemoteValidator,
    validate_branchNumber,
    validate_kvk,
)
from .base import KVKTestMixin, load_json_mock


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
class KvKRemoteValidatorTestCase(KVKTestMixin, SimpleTestCase):
    @requests_mock.Mocker()
    def test_kvkNumber_validator(self, m):
        m.get(
            f"{self.api_root}v1/zoeken?kvkNummer=69599084",
            status_code=200,
            json=load_json_mock("zoeken_response.json"),
        )
        m.get(
            f"{self.api_root}v1/zoeken?kvkNummer=90004760",
            status_code=404,
        )
        m.get(
            f"{self.api_root}v1/zoeken?kvkNummer=68750110",
            status_code=500,
        )

        validator = partial(KVKNumberRemoteValidator(), submission="unused")
        validator("69599084")

        with self.assertRaisesMessage(
            ValidationError, _("%(type)s does not exist.") % {"type": _("KvK number")}
        ):
            validator("90004760")
        with self.assertRaisesMessage(
            ValidationError, _("%(type)s does not exist.") % {"type": _("KvK number")}
        ):
            validator("68750110")

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

    @requests_mock.Mocker()
    def test_kvkNumber_validator_emptyish_results(self, m):
        bad_responses = (
            {"resultaten": []},
            {},
        )
        validate = partial(KVKNumberRemoteValidator(), submission="unused")

        for response_json in bad_responses:
            with self.subTest(response_json=response_json):
                m.get(
                    f"{self.api_root}v1/zoeken?kvkNummer=69599084",
                    json=response_json,
                )

                with self.assertRaises(ValidationError):
                    validate("69599084")

    @requests_mock.Mocker()
    def test_rsin_validator(self, m):
        m.get(
            f"{self.api_root}v1/zoeken?rsin=111222333",
            status_code=200,
            json=load_json_mock("zoeken_response.json"),
        )
        m.get(
            f"{self.api_root}v1/zoeken?rsin=063308836",
            status_code=404,
        )

        validator = partial(KVKRSINRemoteValidator(), submission="unused")
        validator("111222333")

        with self.assertRaisesMessage(
            ValidationError, _("%(type)s does not exist.") % {"type": _("RSIN")}
        ):
            validator("063308836")

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

    @requests_mock.Mocker()
    def test_branchNumber_validator(self, m):
        m.get(
            f"{self.api_root}v1/zoeken?vestigingsnummer=112233445566",
            status_code=200,
            json=load_json_mock("zoeken_response.json"),
        )
        m.get(
            f"{self.api_root}v1/zoeken?vestigingsnummer=665544332211",
            status_code=404,
        )

        validator = partial(KVKBranchNumberRemoteValidator(), submission="unused")
        validator("112233445566")

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
