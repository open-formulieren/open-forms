from pathlib import Path
from unittest import TestCase

from .. import SoftRequiredErrors, get_template_trace_context, supports_multiple
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "soft_required_errors"


class SoftRequiredErrorsTests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "minimal.json")

        self.assertIsInstance(component, SoftRequiredErrors)
        self.assertFalse(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "full.json")

        self.assertIsInstance(component, SoftRequiredErrors)
        self.assertFalse(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "full.json")

    def test_render_templates(self):
        component = SoftRequiredErrors(key="template", html="html")

        component.render_templates(lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.html, "html")

    def test_template_testing(self):
        component = SoftRequiredErrors(key="template", html="<p>Hello there</p>")
        attributes: set[str] = set()

        def do_parse(source: str) -> None:
            trace_context = get_template_trace_context()
            assert trace_context is not None
            attributes.add(trace_context.attribute)

        component.test_templates_with_trace(do_parse)

        self.assertEqual(attributes, set())

    def test_set_default_value_noop(self):
        component = SoftRequiredErrors(
            key="softRequiredErrors",
            html=r"<p>Hello there {{ field_errors }}</p>",
        )

        component.set_default_value(None)

        self.assertFalse(hasattr(component, "default_value"))
