from datetime import UTC, date, datetime
from pathlib import Path
from unittest import TestCase
from zoneinfo import ZoneInfo

from hypothesis import given, strategies as st

from .. import DateTime, get_template_trace_context, supports_multiple
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "datetime"


class DateTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, DateTime)
        self.assertTrue(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, DateTime)
        self.assertTrue(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_cannot_initialize_with_nonsense_default_value(self):
        with self.assertRaises(ValueError):
            DateTime(key="datetime", label="Datetime", multiple=False, default_value=[])

        with self.assertRaises(ValueError):
            DateTime(
                key="datetime",
                label="Datetime",
                multiple=True,
                default_value=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
            )

    def test_render_templates(self):
        component = DateTime(
            key="template",
            label="label",
            description="description",
            tooltip="tooltip",
        )

        component.render_templates(lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.label, "templated: label")
        self.assertEqual(component.description, "templated: description")
        self.assertEqual(component.tooltip, "templated: tooltip")

    def test_template_testing(self):
        component = DateTime(
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
        multiple=...,
        value=st.datetimes(
            timezones=st.one_of(
                st.none(),
                st.just(ZoneInfo("Europe/Amsterdam")),
            )
        ),
    )
    def test_set_default_value(self, multiple: bool, value: date | datetime):
        component = DateTime(
            key="datetime",
            label="Datetime",
            multiple=multiple,
            default_value=[] if multiple else None,
        )
        new_default_value = [value] if multiple else value

        component.set_default_value(new_default_value)

        self.assertEqual(component.default_value, new_default_value)
