from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from rest_framework import serializers

from openforms.accounts.models import User

from ..validators import AllOrNoneRequiredFieldsValidator, ModelValidator


class AllOrNoneRequiredFieldsValidatorSerializer(serializers.Serializer):
    foo = serializers.CharField(required=False, allow_null=True)
    bar = serializers.CharField(required=False, allow_null=True)

    class Meta:
        validators = [AllOrNoneRequiredFieldsValidator("foo", "bar")]


class AllOrNoneRequiredFieldsValidatorTests(SimpleTestCase):
    def test_no_fields_provided(self):
        empty_data_examples = (
            {"foo": None, "bar": None},
            {"foo": None},
            {},
        )
        for empty_data in empty_data_examples:
            with self.subTest(data=empty_data):
                serializer = AllOrNoneRequiredFieldsValidatorSerializer(data=empty_data)

                is_valid = serializer.is_valid()

                self.assertTrue(is_valid)

    def test_all_fields_provided(self):
        serializer = AllOrNoneRequiredFieldsValidatorSerializer(
            data={"foo": "foo", "bar": "bar"}
        )

        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)

    def test_subset_of_fields_provided(self):
        partial_data_examples = (
            {"foo": None, "bar": "bar"},
            {"foo": "foo", "bar": None},
            {"foo": "foo"},
            {"bar": "bar"},
        )
        for incomplete_data in partial_data_examples:
            with self.subTest(data=incomplete_data):
                serializer = AllOrNoneRequiredFieldsValidatorSerializer(
                    data=incomplete_data
                )

                is_valid = serializer.is_valid()

                self.assertFalse(is_valid)


def validate_not_staff(user: User):
    err = ValidationError("May not be staff", code="privileges")
    if user.is_staff:
        raise ValidationError({"is_staff": err})


def validate_non_field_attrs_not_set(user: User):
    if hasattr(user, "extra_field"):
        raise ValidationError("Non-model field attr set", code="bad_attr")


class UserSerializer(serializers.ModelSerializer):
    extra_field = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "is_staff", "extra_field")
        extra_kwargs = {
            "username": {
                "validators": []
            },  # disable unique validator which does queries
        }
        validators = [
            ModelValidator[User](validate_not_staff),
        ]


class ModelValidatorTests(SimpleTestCase):
    def test_runs_validator_function_on_serializer_data(self):
        serializer = UserSerializer(
            data={
                "username": "bob",
                "email": "bob@example.com",
                "is_staff": True,
            }
        )

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("is_staff", serializer.errors)
        self.assertEqual(serializer.errors["is_staff"][0].code, "privileges")

    def test_non_model_field_attrs_not_set(self):
        serializer = UserSerializer(
            data={
                "username": "bob",
                "email": "bob@example.com",
                "is_staff": False,
                "extra_field": "may not be present",
            }
        )

        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)
