from django.test import SimpleTestCase

from rest_framework.serializers import ValidationError

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.typing import JSONObject, JSONValue

from ..service import build_serializer
from ..typing import Component, RadioComponent, TextFieldComponent


def validate_formio_data(components: list[Component], data: JSONValue) -> None:
    context = {"submission": SubmissionFactory.build()}
    serializer = build_serializer(components=components, data=data, context=context)
    serializer.is_valid(raise_exception=True)


class GenericValidationTests(SimpleTestCase):
    """
    Test some generic validation behaviours using anecdotal examples.

    Tests in this class are aimed towards some patterns, but use specific component
    types as an easy-to-follow-and-debug example. Full coverage needs to be guaranteed
    through the YAML-based tests or component-type specific test cases like below.
    """

    def test_component_without_validate_information(self):
        component: RadioComponent = {
            "type": "radio",
            "key": "radio",
            "label": "Test",
            "values": [],
        }

        try:
            validate_formio_data([component], {"radio": ""})
        except ValidationError as exc:
            raise self.failureException(
                "Expected component to pass validation"
            ) from exc

    def test_multiple_respected(self):
        """
        Test that component ``multiple: true`` is correctly validated.

        Many components support multiple, but not all of them. The value data structure
        changes for multiple, and the invalid param names should change accordingly.
        """
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "textMultiple",
            "label": "Text multiple",
            "multiple": True,
            "validate": {
                "required": True,
                "maxLength": 3,
            },
            "defaultValue": [],
        }
        data: JSONObject = {
            "textMultiple": [
                "ok",
                "not okay",
                "",
            ],
        }

        with self.assertRaises(ValidationError) as exc_context:
            validate_formio_data([component], data)

        detail = exc_context.exception.detail
        assert isinstance(detail, dict)
        assert "textMultiple" in detail
        nested = detail["textMultiple"]
        assert isinstance(nested, dict)

        self.assertEqual(list(nested.keys()), [1, 2])

        with self.subTest("Error for item at index 1"):
            self.assertEqual(len(errors := nested[1]), 1)
            self.assertEqual(errors[0].code, "max_length")  # type: ignore

        with self.subTest("Error for item at index 2"):
            self.assertEqual(len(errors := nested[2]), 1)
            self.assertEqual(errors[0].code, "blank")  # type: ignore

    def test_key_with_nested_structure(self):
        component: Component = {
            "type": "textfield",
            "key": "parent.nested",
            "label": "Special key",
            "validate": {
                "maxLength": 2,
            },
        }
        data: JSONObject = {"parent": {"nested": "foo"}}

        with self.assertRaises(ValidationError) as exc_context:
            validate_formio_data([component], data)

        detail = exc_context.exception.detail
        assert isinstance(detail, dict)
        assert "parent" in detail
        self.assertIn("parent", detail)
        self.assertIn("nested", detail["parent"])
        err_code = detail["parent"]["nested"][0].code
        self.assertEqual(err_code, "max_length")
