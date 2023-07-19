from django.test import SimpleTestCase

from rest_framework.serializers import ValidationError

from ..validation import validate_formio_data


class FormioValidationTests(SimpleTestCase):
    def test_textfield_required_validation(self):
        component = {"type": "textfield", "key": "foo", "validate": {"required": True}}

        invalid_values = [
            {},
            {"foo": ""},
            {"foo": None},
        ]

        for data in invalid_values:
            with self.subTest(data=data):
                with self.assertRaises(ValidationError) as exc_detail:
                    validate_formio_data([component], data)

                self.assertEqual(exc_detail.exception.detail["0"].code, "required")  # type: ignore

    def test_textfield_max_length(self):
        component = {"type": "textfield", "key": "foo", "validate": {"maxLength": 3}}

        with self.assertRaises(ValidationError) as exc_detail:
            validate_formio_data([component], {"foo": "barbaz"})

        self.assertEqual(exc_detail.exception.detail["0"].code, "max_length")  # type: ignore

    def test_component_without_validate_information(self):
        component = {"type": "radio", "key": "radio", "values": []}

        try:
            validate_formio_data([component], {"radio": ""})
        except ValidationError as exc:
            raise self.failureException(
                "Expected component to pass validation"
            ) from exc
