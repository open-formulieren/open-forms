from pathlib import Path
from unittest import TestCase

from .. import (
    Column,
    Columns,
    Email,
    TextField,
    get_template_trace_context,
    supports_multiple,
)
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "columns"


class ColumnsTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, Columns)
        self.assertFalse(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, Columns)
        self.assertFalse(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_template_testing(self):
        component = Columns(key="template", columns=[])
        attributes: set[str] = set()

        def do_parse(source: str) -> None:
            trace_context = get_template_trace_context()
            assert trace_context is not None
            attributes.add(trace_context.attribute)

        component.test_templates_with_trace(do_parse)

        self.assertEqual(attributes, set())

    def test_set_default_value_noop(self):
        component = Columns(key="Columns", columns=[])

        component.set_default_value(None)

        self.assertFalse(hasattr(component, "default_value"))

    def test_iter_children_recurses_into_columns(self):
        component = Columns(
            key="columns",
            columns=[
                Column(size=6, components=[Email(key="email", label="Email")]),
                Column(size=6, components=[TextField(key="textfield", label="Text")]),
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
