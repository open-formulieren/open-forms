from pathlib import Path
from unittest import TestCase

from .. import (
    Email,
    Fieldset,
    TextField,
    get_template_trace_context,
    supports_multiple,
)
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "fieldset"


class FieldsetTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, Fieldset)
        self.assertFalse(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, Fieldset)
        self.assertFalse(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_render_templates(self):
        component = Fieldset(
            key="template",
            label="label",
            tooltip="tooltip",
            components=[],
        )

        component.render_templates(lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.label, "templated: label")
        self.assertEqual(component.tooltip, "templated: tooltip")

    def test_template_testing(self):
        component = Fieldset(key="template", label="Fieldset", components=[])
        attributes: set[str] = set()

        def do_parse(source: str) -> None:
            trace_context = get_template_trace_context()
            assert trace_context is not None
            attributes.add(trace_context.attribute)

        component.test_templates_with_trace(do_parse)

        self.assertEqual(attributes, {"label", "tooltip"})

    def test_set_default_value_noop(self):
        component = Fieldset(key="fieldset", label="Fieldset", components=[])

        component.set_default_value(None)

        self.assertFalse(hasattr(component, "default_value"))

    def test_iter_children_recurses_into_Fieldset(self):
        component = Fieldset(
            key="fieldset",
            label="Fieldset",
            components=[
                Email(key="email", label="Email"),
                TextField(key="textfield", label="Text"),
            ],
        )

        children = [child for child, _ in component.iter_children()]

        self.assertEqual(
            children,
            [
                Email(key="email", label="Email"),
                TextField(key="textfield", label="Text"),
            ],
        )
