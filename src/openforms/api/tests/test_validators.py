from django.test import SimpleTestCase

from rest_framework import serializers

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
