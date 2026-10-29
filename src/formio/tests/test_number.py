from datetime import date, datetime, time
from pathlib import Path
from unittest import TestCase

from hypothesis import given, strategies as st

from .. import Number, get_template_trace_context, supports_multiple
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "number"


class NumberTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, Number)
        self.assertFalse(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, Number)
        self.assertFalse(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_render_templates(self):
        component = Number(
            key="template",
            label="label template",
            description="description template",
            tooltip="tooltip template",
        )

        component.render_templates(do_render=lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.label, "templated: label template")
        self.assertEqual(component.description, "templated: description template")
        self.assertEqual(component.tooltip, "templated: tooltip template")

    def test_template_testing(self):
        component = Number(
            key="template",
            label="label",
            description="description",
            tooltip="tooltip",
        )
        attributes: set[str] = set()

        def do_parse(source: str) -> None:
            trace_context = get_template_trace_context()
            assert trace_context is not None
            attributes.add(trace_context.attribute)

        component.test_templates_with_trace(do_parse)

        self.assertEqual(attributes, {"label", "description", "tooltip"})

    @given(
        value=st.one_of(
            st.none(), st.integers(), st.floats(allow_infinity=False, allow_nan=False)
        )
    )
    def test_set_default_value(self, value: int | float | None):  # noqa: PYI041
        component = Number(key="number", label="Number", default_value=None)

        component.set_default_value(value)

        self.assertEqual(component.default_value, value)

    @given(value=...)
    def test_it_does_not_crash_with_wrong_default_value_data_type(
        self,
        value: str | date | datetime | time,
    ):
        component = Number(key="number", label="Number", default_value=None)

        component.set_default_value(value)

        self.assertIsNone(component.default_value)
