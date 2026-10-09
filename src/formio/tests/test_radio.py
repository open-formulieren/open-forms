from pathlib import Path
from unittest import TestCase

from hypothesis import given

from .. import Option, Radio, get_template_trace_context, supports_multiple
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "radio"


class RadioTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, Radio)
        self.assertFalse(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, Radio)
        self.assertFalse(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_incomplete_data_src_configuration(self):
        with self.subTest("variable"):
            with self.assertRaises(ValueError):
                load_json(TEST_FILES / "dataSrc-variable-incomplete.json")

            component = load_json(TEST_FILES / "dataSrc-variable-complete.json")

            assert isinstance(component, Radio)
            self.assertEqual(component.open_forms.data_src, "variable")

        # TODO: make more strict and fail hard?
        with self.subTest("incomplete referenceLists"):
            component = load_json(TEST_FILES / "dataSrc-referenceLists-incomplete.json")

            assert isinstance(component, Radio)
            self.assertEqual(component.open_forms.data_src, "referenceLists")

        with self.subTest("complete referenceLists"):
            component = load_json(TEST_FILES / "dataSrc-referenceLists-complete.json")

            assert isinstance(component, Radio)
            self.assertEqual(component.open_forms.data_src, "referenceLists")

    def test_render_templates(self):
        component = Radio(
            key="template",
            label="label",
            description="description",
            tooltip="tooltip",
            values=[Option(value="someValue", label="option label")],
        )

        component.render_templates(lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.label, "templated: label")
        self.assertEqual(component.description, "templated: description")
        self.assertEqual(component.tooltip, "templated: tooltip")
        self.assertEqual(component.values[0].label, "templated: option label")

    def test_template_testing(self):
        component = Radio(
            key="template",
            label="label",
            description="description",
            tooltip="tooltip",
            values=[Option(value="someValue", label="option label")],
        )
        attributes: set[str] = set()

        def do_parse(source: str) -> None:
            trace_context = get_template_trace_context()
            assert trace_context is not None
            attributes.add(trace_context.attribute)

        component.test_templates_with_trace(do_parse)

        self.assertEqual(attributes, {"label", "description", "tooltip", "values"})

    @given(value=...)
    def test_set_default_value(self, value: str):
        component = Radio(key="radio", label="Radio", default_value="")

        component.set_default_value(value)

        self.assertEqual(component.default_value, value)
