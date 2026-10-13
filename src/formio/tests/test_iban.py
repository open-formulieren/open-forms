from datetime import date, datetime, time
from pathlib import Path
from unittest import TestCase

from hypothesis import given

from .. import IBAN, get_template_trace_context, supports_multiple
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "iban"


class IbanTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, IBAN)
        self.assertTrue(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, IBAN)
        self.assertTrue(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_cannot_initialize_with_nonsense_default_value(self):
        with self.assertRaises(ValueError):
            IBAN(key="iban", label="Iban", multiple=False, default_value=[])

        with self.assertRaises(ValueError):
            IBAN(key="iban", label="Iban", multiple=True, default_value="")

    @given(multiple=...)
    def test_render_templates(self, multiple: bool):
        component = IBAN(
            key="template",
            multiple=multiple,
            label="label template",
            description="description template",
            tooltip="tooltip template",
            default_value=["default_value template"]
            if multiple
            else "default_value template",
        )

        component.render_templates(do_render=lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.label, "templated: label template")
        self.assertEqual(component.description, "templated: description template")
        self.assertEqual(component.tooltip, "templated: tooltip template")
        self.assertEqual(
            component.default_value,
            ["templated: default_value template"]
            if multiple
            else "templated: default_value template",
        )

    def test_template_testing(self):
        component = IBAN(
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
        component = IBAN(
            key="iban",
            label="IBAN",
            multiple=multiple,
            default_value=[] if multiple else "",
        )
        new_default_value = [value] if multiple else value

        component.set_default_value(new_default_value)

        self.assertEqual(component.default_value, new_default_value)

    @given(multiple=..., value=...)
    def test_set_default_value_empty(self, multiple: bool, value: str):
        component = IBAN(
            key="iban",
            label="IBAN",
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
        component = IBAN(
            key="iban",
            label="IBAN",
            multiple=multiple,
            default_value=original_default_value,
        )
        new_default_value = [value] if multiple else value

        component.set_default_value(new_default_value)

        self.assertEqual(component.default_value, original_default_value)
