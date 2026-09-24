from pathlib import Path
from unittest import TestCase

import msgspec

from .. import FormioConfiguration

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
