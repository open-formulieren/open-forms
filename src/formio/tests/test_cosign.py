from pathlib import Path
from unittest import TestCase

from .. import CosignV1, CosignV2, get_template_trace_context, supports_multiple
from .helpers import ComponentAssertions, load_json

TEST_FILES = Path(__file__).parent.resolve() / "files" / "cosign"


class CosignV1Tests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "cosign_v1_minimal.json")

        self.assertIsInstance(component, CosignV1)
        self.assertFalse(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "cosign_v1_full.json")

        self.assertIsInstance(component, CosignV1)
        self.assertFalse(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "cosign_v1_full.json")

    def test_render_templates(self):
        component = CosignV1(
            key="template",
            label="label",
            description="description",
        )

        component.render_templates(lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.label, "templated: label")
        self.assertEqual(component.description, "templated: description")

    def test_template_testing(self):
        component = CosignV1(
            key="template",
            label="label",
            description="description",
        )
        attributes: set[str] = set()

        def do_parse(source: str) -> None:
            trace_context = get_template_trace_context()
            assert trace_context is not None
            attributes.add(trace_context.attribute)

        component.test_templates_with_trace(do_parse)

        self.assertEqual(attributes, {"label", "description"})


class CosignV2Tests(ComponentAssertions, TestCase):
    def test_loads_minimal_json_definition(self):
        component = load_json(TEST_FILES / "cosign_v2_minimal.json")

        self.assertIsInstance(component, CosignV2)
        self.assertFalse(supports_multiple(component))

    def test_loads_full_json_definition(self):
        component = load_json(TEST_FILES / "cosign_v2_full.json")

        self.assertIsInstance(component, CosignV2)
        self.assertFalse(supports_multiple(component))

    def test_roundtrip(self):
        self.assertRoundtripInvariant(TEST_FILES / "cosign_v2_full.json")

    def test_render_templates(self):
        component = CosignV2(
            key="template",
            label="label",
            description="description",
            tooltip="tooltip",
            default_value="default_value",
        )

        component.render_templates(lambda tpl: f"templated: {tpl}")

        self.assertEqual(component.label, "templated: label")
        self.assertEqual(component.description, "templated: description")
        self.assertEqual(component.tooltip, "templated: tooltip")
        self.assertEqual(component.default_value, "templated: default_value")

    def test_template_testing(self):
        component = CosignV2(
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

    def test_set_default_value(self):
        with self.subTest("string value"):
            component = CosignV2(key="cosignV2", label="Cosign V2", default_value="")

            component.set_default_value("info@example.com")

            self.assertEqual(component.default_value, "info@example.com")

        with self.subTest("empty value"):
            component = CosignV2(
                key="cosignV2", label="Cosign V2", default_value="info@example.com"
            )

            component.set_default_value(None)

            self.assertEqual(component.default_value, "")
