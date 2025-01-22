from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from rest_framework import serializers

from openforms.accounts.models import User

from ..validators import AllOrNoneTruthyFieldsValidator, ModelValidator


class AllOrNoneTruthyFieldsValidatorSerializer(serializers.Serializer):
    foo = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    bar = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        validators = [AllOrNoneTruthyFieldsValidator("foo", "bar")]


class AllOrNoneTruthyFieldsValidatorTests(SimpleTestCase):
    def test_it_validates_when_no_values_provided(self):
        empty_data_examples = (
            {"foo": None, "bar": None},
            {"foo": None},
            {"foo": ""},
            {},
        )
        for empty_data in empty_data_examples:
            with self.subTest(data=empty_data):
                serializer = AllOrNoneTruthyFieldsValidatorSerializer(data=empty_data)

                is_valid = serializer.is_valid()

                self.assertTrue(is_valid)

    def test_it_validates_when_values_for_all_fields_provided(self):
        serializer = AllOrNoneTruthyFieldsValidatorSerializer(
            data={"foo": "foo", "bar": "bar"}
        )

        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)

    def test_it_doesnt_validate_when_only_subset_of_values_provided(self):
        partial_data_examples = (
            {"foo": None, "bar": "bar"},
            {"foo": "", "bar": "bar"},
            {"foo": "foo", "bar": None},
            {"foo": "foo"},
            {"bar": "bar"},
        )
        for incomplete_data in partial_data_examples:
            with self.subTest(data=incomplete_data):
                serializer = AllOrNoneTruthyFieldsValidatorSerializer(
                    data=incomplete_data
                )

                is_valid = serializer.is_valid()

                self.assertFalse(is_valid)

    def test_behaviour_with_boolean_fields(self):
        class Serializer(serializers.Serializer):
            bool1 = serializers.BooleanField(required=False, allow_null=True)
            bool2 = serializers.BooleanField(required=False, allow_null=True)

            class Meta:
                validators = [AllOrNoneTruthyFieldsValidator("bool1", "bool2")]

        with self.subTest("None provided"):
            serializer1 = Serializer(data={})

            self.assertTrue(serializer1.is_valid())

        with self.subTest("Both truthy provided"):
            serializer2 = Serializer(data={"bool1": True, "bool2": True})

            self.assertTrue(serializer2.is_valid())

        with self.subTest("One truthy, one falsy provided"):
            serializer3 = Serializer(data={"bool1": True, "bool2": False})

            self.assertFalse(serializer3.is_valid())

        with self.subTest("Only one truthy provided"):
            serializer4 = Serializer(data={"bool1": True})

            self.assertFalse(serializer4.is_valid())

        with self.subTest("Only one false provided"):
            serializer5 = Serializer(data={"bool2": False})

            self.assertTrue(serializer5.is_valid())

        with self.subTest("Null provided"):
            serializer6 = Serializer(data={"bool2": False, "bool1": None})

            self.assertTrue(serializer6.is_valid())


def validate_not_staff(user: User):
    err = ValidationError("May not be staff", code="privileges")
    if user.is_staff:
        raise ValidationError({"is_staff": err})


class UserSerializer(serializers.ModelSerializer):
    extra_field = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("username", "email", "is_staff", "extra_field")
        extra_kwargs = {
            "username": {
                "validators": []
            },  # disable unique validator which does queries
            "email": {"validators": []},  # disable unique validator which does queries
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
