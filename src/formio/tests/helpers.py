from pathlib import Path
from typing import TYPE_CHECKING
from unittest import TestCase

import msgspec

from .. import AnyComponent

if TYPE_CHECKING:  # pragma: no cover
    BaseTestCase = TestCase
else:
    BaseTestCase = object

component_decoder = msgspec.json.Decoder(type=AnyComponent)
encoder = msgspec.json.Encoder()

plain_json_decoder = msgspec.json.Decoder()


def load_json(file_path: Path) -> AnyComponent:
    """
    Load the specified JSON and convert to a component definition struct.
    """
    binary_data = file_path.read_bytes()
    return component_decoder.decode(binary_data)


def dump_json(obj: AnyComponent) -> bytes:
    return encoder.encode(obj)


class ComponentAssertions(BaseTestCase):
    def assertRoundtripInvariant(self, file_path: Path):
        self.maxDiff = None

        source_bytes = file_path.read_bytes()
        component = component_decoder.decode(source_bytes)
        dumped_json = encoder.encode(component)
        # we load again with builtins to be able to display nice diffs
        self.assertEqual(
            plain_json_decoder.decode(dumped_json),
            plain_json_decoder.decode(source_bytes),
        )
