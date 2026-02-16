from collections.abc import Sequence

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings

from unittest_parametrize import ParametrizedTestCase, parametrize

from ..validators import IdTemplateValidator, validate_bsn, validate_iban, validate_rsin


class BSNValidatorTestCase(SimpleTestCase):
    @staticmethod
    def test_valid_bsns():
        validate_bsn("063308836")
        validate_bsn("619183020")

    def test_invalid_bsns(self):
        with self.assertRaises(ValidationError):
            validate_bsn("06330883")

        with self.assertRaises(ValidationError):
            validate_bsn("063a08836")

        with self.assertRaises(ValidationError):
            validate_bsn("063-08836")


class RSINValidatorTestCase(SimpleTestCase):
    @staticmethod
    def test_valid_bsns():
        validate_rsin("063308836")
        validate_rsin("619183020")

    def test_invalid_bsns(self):
        with self.assertRaises(ValidationError):
            validate_rsin("06330883")

        with self.assertRaises(ValidationError):
            validate_rsin("063a08836")

        with self.assertRaises(ValidationError):
            validate_rsin("063-08836")


class IBANValidatorTestCase(SimpleTestCase):
    def test_valid_ibans(self):
        validate_iban("NL02ABNA0123456789")
        validate_iban("NL14 ABNA 1238 8878 00")

    def test_invalid_ibans(self):
        with self.assertRaises(ValidationError):
            validate_iban("NL12 3456 789I I987 6999")

        with self.assertRaises(ValidationError):
            validate_iban("DX89 3704 0044 0532 0130 00")

        with self.assertRaises(ValidationError):
            validate_iban("DE20 2909 0900 8840 0170 9000")

        with self.assertRaises(ValidationError):
            validate_iban("DEo20 2909 0900 8840 0170 00")


class IDTemplateValidatorTests(ParametrizedTestCase, SimpleTestCase):
    def test_uid_present(self):
        valid = "{uid}"
        with self.subTest(value=valid):
            IdTemplateValidator()(valid)

        invalid = "other_things"
        with self.subTest(value=invalid):
            with self.assertRaises(ValidationError):
                IdTemplateValidator()(invalid)

    def test_valid_templates(self):
        valid = [
            "{uid}",
            "{uid}ab",
            "{uid}12",
            "{uid}ab12",
            "{uid}a-.///---_",
            # placeholders:
            "{uid}{year}",
            "{year}{public_reference}{uid}",
        ]

        for value in valid:
            with self.subTest(value=value):
                IdTemplateValidator()(value)

    def test_raises_for_invalid_prefixes(self):
        invalid = [
            " {uid}",
            "aa {uid}",
            " aa{uid}",
            "{yearrr{uid}",
            "{bad}{uid}",
        ]

        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    IdTemplateValidator()(value)

    @parametrize(
        "allowed_groups,expected_error",
        [
            (
                (),
                "The template may only consist of alphanumeric characters.",
            ),
            (
                ("-"),
                "The template may only consist of alphanumeric and - characters.",
            ),
            (
                ("-", "_", "/"),
                "The template may only consist of alphanumeric, -, _ and / characters.",
            ),
        ],
    )
    @override_settings(LANGUAGE_CODE="en")
    def test_validation_error_messages(
        self,
        allowed_groups: Sequence[str],
        expected_error: str,
    ):
        value = "{foobarbaz}{uid}trigger$$$"
        validator = IdTemplateValidator(allowed_groups=allowed_groups)

        with self.assertRaisesMessage(ValidationError, expected_message=expected_error):
            validator(value)
