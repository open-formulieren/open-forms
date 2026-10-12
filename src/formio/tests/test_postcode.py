from datetime import date, datetime, time
from pathlib import Path
from unittest import TestCase

from hypothesis import given

from .. import Postcode, get_template_trace_context, supports_multiple
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "postcode"


class PostcodeTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, Postcode)
        self.assertTrue(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, Postcode)
        self.assertTrue(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_cannot_initialize_with_nonsense_default_value(self):
        with self.assertRaises(ValueError):
            Postcode(
                key="postcode",
                label="Postcode",
                multiple=False,
                default_value=[],
            )

        with self.assertRaises(ValueError):
            Postcode(
                key="postcode",
                label="Postcode",
                multiple=True,
                default_value="",
            )

    @given(multiple=...)
    def test_render_templates(self, multiple: bool):
        component = Postcode(
            key="template",
            multiple=multiple,
            label="label",
            description="description",
            tooltip="tooltip",
            default_value=["default_value"] if multiple else "default_value",
        )

        component.render_templates(lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.label, "templated: label")
        self.assertEqual(component.description, "templated: description")
        self.assertEqual(component.tooltip, "templated: tooltip")
        self.assertEqual(
            component.default_value,
            ["templated: default_value"] if multiple else "templated: default_value",
        )

    def test_template_testing(self):
        component = Postcode(
            key="template",
            label="label",
            description="description",
            tooltip="tooltip",
            default_value="default_value",
        )
        attributes: set[str] = set()

        def do_parse(source: str) -> None:
            trace_context = get_template_trace_context()
            assert trace_context is not None
            attributes.add(trace_context.attribute)

        component.test_templates_with_trace(do_parse)

        self.assertEqual(
            attributes, {"label", "description", "tooltip", "default_value"}
        )

    @given(multiple=..., value=...)
    def test_set_default_value(self, multiple: bool, value: str):
        component = Postcode(
            key="postcode",
            label="Postcode",
            multiple=multiple,
            default_value=[] if multiple else "",
        )
        new_default_value = [value] if multiple else value

        component.set_default_value(new_default_value)

        self.assertEqual(component.default_value, new_default_value)

    @given(multiple=..., value=...)
    def test_set_default_value_empty(self, multiple: bool, value: str):
        component = Postcode(
            key="postcode",
            label="Postcode",
            multiple=multiple,
            default_value=[value] if multiple else value,
        )

        component.set_default_value(None)

        self.assertEqual(component.default_value, [] if multiple else "")

    @given(multiple=..., value=...)
    def test_it_does_not_crash_with_wrong_default_value_data_type(
        self,
        multiple: bool,
        value: None | date | datetime | time | int | bool,
    ):
        original_default_value = [] if multiple else ""
        component = Postcode(
            key="postcode",
            label="Postcode",
            multiple=multiple,
            default_value=original_default_value,
        )
        new_default_value = [value] if multiple else value

        component.set_default_value(new_default_value)

        self.assertEqual(component.default_value, original_default_value)
