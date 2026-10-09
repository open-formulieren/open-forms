from pathlib import Path
from unittest import TestCase

from .. import (
    EditGrid,
    Email,
    TextField,
    get_template_trace_context,
    supports_multiple,
)
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "editgrid"


class EditGridTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, EditGrid)
        self.assertFalse(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, EditGrid)
        self.assertFalse(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_render_templates(self):
        component = EditGrid(
            key="template",
            label="label",
            description="description",
            tooltip="tooltip",
            group_label="group_label",
            components=[],
        )

        component.render_templates(lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.label, "templated: label")
        self.assertEqual(component.description, "templated: description")
        self.assertEqual(component.tooltip, "templated: tooltip")
        self.assertEqual(component.group_label, "templated: group_label")

    def test_template_testing(self):
        component = EditGrid(
            key="template", label="Repeating group", group_label="Item", components=[]
        )
        attributes: set[str] = set()

        def do_parse(source: str) -> None:
            trace_context = get_template_trace_context()
            assert trace_context is not None
            attributes.add(trace_context.attribute)

        component.test_templates_with_trace(do_parse)

        self.assertEqual(attributes, {"label", "description", "tooltip", "group_label"})

    def test_set_default_value_noop(self):
        component = EditGrid(
            key="editgrid", label="Repeating group", group_label="Item", components=[]
        )

        with self.assertRaises(NotImplementedError):
            component.set_default_value(None)

        self.assertFalse(hasattr(component, "default_value"))

    def test_iter_children_recurses_into_EditGrid(self):
        component = EditGrid(
            key="editgrid",
            label="Repeating group",
            group_label="Item",
            components=[
                Email(key="email", label="Email"),
                TextField(key="textfield", label="Text"),
            ],
        )

        children = list(component.iter_children())

        self.assertEqual(
            children,
            [
                (Email(key="email", label="Email"), "editgrid"),
                (
                    TextField(key="textfield", label="Text"),
                    "editgrid",
                ),
            ],
        )
