from datetime import date, datetime, time
from pathlib import Path
from unittest import TestCase
from zoneinfo import ZoneInfo

from hypothesis import given, settings, strategies as st

from .. import Date, get_template_trace_context, supports_multiple
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "date"


class DateTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, Date)
        self.assertTrue(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, Date)
        self.assertTrue(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_cannot_initialize_with_nonsense_default_value(self):
        with self.assertRaises(ValueError):
            Date(key="date", label="Date", multiple=False, default_value=[])

        with self.assertRaises(ValueError):
            Date(
                key="date", label="Date", multiple=True, default_value=date(2026, 1, 1)
            )

    def test_render_templates(self):
        component = Date(
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
        component = Date(
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

    @settings(deadline=None)
    @given(
        multiple=...,
        value=st.one_of(
            st.dates(),
            st.datetimes(
                timezones=st.one_of(
                    st.none(),
                    st.just(ZoneInfo("Europe/Amsterdam")),
                )
            ),
        ),
    )
    def test_set_default_value(self, multiple: bool, value: date | datetime):
        component = Date(
            key="date",
            label="Date",
            multiple=multiple,
            default_value=[] if multiple else None,
        )
        _expected_default_value = value.date() if isinstance(value, datetime) else value
        new_default_value = [value] if multiple else value
        expected_default_value = (
            [_expected_default_value] if multiple else _expected_default_value
        )

        component.set_default_value(new_default_value)

        self.assertEqual(component.default_value, expected_default_value)

    @given(multiple=..., value=...)
    def test_it_does_not_crash_with_wrong_default_value_data_type(
        self,
        multiple: bool,
        value: str | None | time | int | bool,
    ):
        original_default_value = [] if multiple else None
        component = Date(
            key="date",
            label="Date",
            multiple=multiple,
            default_value=original_default_value,
        )
        new_default_value = [value] if multiple else value

        component.set_default_value(new_default_value)

        self.assertEqual(component.default_value, original_default_value)
