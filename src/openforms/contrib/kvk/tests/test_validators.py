from django.core.exceptions import ValidationError
from django.test import TestCase

import requests_mock
from zgw_consumers.test import mock_service_oas_get

from openforms.contrib.kvk.tests.base import KVKTestMixin
from openforms.contrib.kvk.validators import (
    KVKBranchNumberRemoteValidator,
    KVKNumberRemoteValidator,
    KVKRSINRemoteValidator,
    validate_branchNumber,
    validate_kvk,
)


class KvKValidatorTestCase(TestCase):
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


class KvKRemoteValidatorTestCase(KVKTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_kvkNumber_validator(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="kvkapiprofileoas3")
        m.get(
            "https://companies/api/v2/testprofile/companies?kvkNumber=69599084",
            status_code=200,
            json=self.load_json_mock("companies.json"),
        )
        m.get(
            "https://companies/api/v2/testprofile/companies?kvkNumber=90004760",
            status_code=404,
        )
        m.get(
            "https://companies/api/v2/testprofile/companies?kvkNumber=68750110",
            status_code=500,
        )
        validator = KVKNumberRemoteValidator()
        validator("69599084")
        with self.assertRaisesMessage(ValidationError, "KVK number does not exist."):
            validator("90004760")
        with self.assertRaisesMessage(ValidationError, "KVK number does not exist."):
            validator("68750110")

        with self.assertRaisesMessage(
            ValidationError, "KVK number should have 8 characters."
        ):
            validator("123")
        with self.assertRaisesMessage(ValidationError, "Expected a numerical value."):
            validator("bork")

    @requests_mock.Mocker()
    def test_rsin_validator(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="kvkapiprofileoas3")
        m.get(
            "https://companies/api/v2/testprofile/companies?rsin=111222333",
            status_code=200,
            json=self.load_json_mock("companies.json"),
        )
        m.get(
            "https://companies/api/v2/testprofile/companies?rsin=063308836",
            status_code=404,
        )
        validator = KVKRSINRemoteValidator()
        validator("111222333")
        with self.assertRaisesMessage(ValidationError, "RSIN does not exist."):
            validator("063308836")

        with self.assertRaisesMessage(
            ValidationError, "RSIN should have 9 characters."
        ):
            validator("123")
        with self.assertRaisesMessage(ValidationError, "Expected a numerical value."):
            validator("bork")

    @requests_mock.Mocker()
    def test_branchNumber_validator(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="kvkapiprofileoas3")
        m.get(
            "https://companies/api/v2/testprofile/companies?branchNumber=112233445566",
            status_code=200,
            json=self.load_json_mock("companies.json"),
        )
        m.get(
            "https://companies/api/v2/testprofile/companies?branchNumber=665544332211",
            status_code=404,
        )
        validator = KVKBranchNumberRemoteValidator()
        validator("112233445566")
        with self.assertRaisesMessage(ValidationError, "Branch number does not exist."):
            validator("665544332211")

        with self.assertRaisesMessage(
            ValidationError, "Branch number should have 12 characters."
        ):
            validator("123")
        with self.assertRaisesMessage(ValidationError, "Expected a numerical value."):
            validator("bork")
