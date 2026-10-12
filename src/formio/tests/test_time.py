from datetime import UTC, time
from pathlib import Path
from unittest import TestCase
from zoneinfo import ZoneInfo

from hypothesis import given, strategies as st

from .. import Time, get_template_trace_context, supports_multiple
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "time"


class DateTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, Time)
        self.assertTrue(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, Time)
        self.assertTrue(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_cannot_initialize_with_nonsense_default_value(self):
        with self.assertRaises(ValueError):
            Time(key="time", label="Time", multiple=False, default_value=[])

        with self.assertRaises(ValueError):
            Time(
                key="time",
                label="Time",
                multiple=True,
                default_value=time(0, 0, 0, tzinfo=UTC),
            )

    def test_render_templates(self):
        component = Time(
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
        component = Time(
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
        value=st.times(
            timezones=st.one_of(
                st.none(),
                st.just(ZoneInfo("Europe/Amsterdam")),
            )
        ),
    )
    def test_set_default_value(self, multiple: bool, value: time):
        component = Time(
            key="time",
            label="Time",
            multiple=multiple,
            default_value=[] if multiple else None,
        )
        new_default_value = [value] if multiple else value

        component.set_default_value(new_default_value)

        self.assertEqual(component.default_value, new_default_value)
