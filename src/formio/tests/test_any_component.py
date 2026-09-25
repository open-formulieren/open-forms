from collections.abc import Iterator
from pathlib import Path
from unittest import TestCase

import msgspec
from hypothesis import HealthCheck, given, settings, strategies as st

from .. import Content, Email, FormioConfiguration, Textarea, TextField
from ..base_component import Component
from .search_strategies import formio_key

SRC_DIR = Path(__file__).parent.parent.parent.resolve()
TEST_FILES_DIR = SRC_DIR / "openforms" / "formio" / "formatters" / "tests" / "files"

CONFIGURATION_FILES = (
    TEST_FILES_DIR / "all_components.json",
    TEST_FILES_DIR / "kitchensink_components.json",
)

decoder = msgspec.json.Decoder(type=FormioConfiguration)


class AnyComponentTests(TestCase):
    def test_load_existing_formio_definitions_from_json(self):
        for path in CONFIGURATION_FILES:
            with self.subTest(path=path):
                try:
                    decoder.decode(path.read_bytes())
                except msgspec.ValidationError as exc:
                    raise self.failureException(
                        "Component definitions unexpectedly failed to parse."
                    ) from exc

    def test_can_read_component_type(self):
        path = TEST_FILES_DIR / "all_components.json"
        configuration = decoder.decode(path.read_bytes())

        for component in configuration.components:
            with self.subTest(component=component.key):
                component_type = component.type

                self.assertIsInstance(component_type, str)
                self.assertNotEqual(component_type, "unknown")
                self.assertGreater(len(component_type), 0)

    @settings(suppress_health_check=[HealthCheck.too_slow])
    @given(
        # subset of component types so that we know we only have to provide key + label
        component_cls=st.sampled_from([TextField, Email, Textarea]),
        key=formio_key(),
    )
    def test_repr_displays_type_and_key(
        self,
        component_cls: type[TextField | Email | Textarea],
        key: str,
    ):
        component = component_cls(key=key, label="Test component")

        str_repr = repr(component)

        self.assertIsInstance(str_repr, str)
        self.assertIn(key, str_repr)
        self.assertIn(str(component_cls.__name__), str_repr)

    def test_components_always_report_something_label_like(self):
        with self.subTest("component with label"):
            textfield = TextField(key="withLabel", label="Hiya!")

            label = textfield.get_label()

            self.assertEqual(label, "Hiya!")

        with self.subTest("component without label"):
            content = Content(key="withoutLabel", html="")

            label = content.get_label()

            self.assertEqual(label, "withoutLabel")

    def test_looping_over_children_yields_any_component(self):
        components = (
            component
            for path in CONFIGURATION_FILES
            for component in (decoder.decode(path.read_bytes())).components
        )

        def _iter_components_and_children() -> Iterator[Component]:
            for component in components:
                yield component
                for child, _ in component.iter_children():
                    yield child

        for component in _iter_components_and_children():
            self.assertIsInstance(component, Component)
            self.assertIsInstance(component.key, str)
            self.assertGreater(len(component.key), 0)
