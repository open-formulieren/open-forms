"""
Test the top-level ``formio`` module Python API.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal
from unittest import TestCase

import msgspec
from hypothesis import given

from .. import convert_component, convert_components, to_python
from ..base_component import Component
from ..typing import ComponentDict
from .helpers import load_json

TEST_FILES = Path(__file__).parent.resolve() / "files"

type Subdir = Literal[
    "address_nl",
    "bsn",
    "checkbox",
    "children",
    "columns",
    "content",
    # "cosign",  # different file names :)
    "currency",
    "customer_profile",
    "date",
    "datetime",
    "editgrid",
    "email",
    "fieldset",
    "file",
    "iban",
    "licenseplate",
    "map",
    "np_family_members",
    "number",
    "partners",
    "phone_number",
    "postcode",
    "radio",
    "select",
    "selectboxes",
    "signature",
    "soft_required_errors",
    "textarea",
    "textfield",
    "time",
]


json_decoder = msgspec.json.Decoder()
"""
Plain JSON -> builtins decoder.
"""


class PublicAPITests(TestCase):
    @given(subdir=..., file_name=...)
    def test_convert_single_component(
        self, subdir: Subdir, file_name: Literal["full.json", "minimal.json"]
    ):
        # grab a random test file and ensure it can be converted to msgspec definition
        full_path = TEST_FILES / subdir / file_name
        json_data = full_path.read_bytes()
        component_dict: ComponentDict = json_decoder.decode(json_data)

        component = convert_component(component_dict)

        self.assertIsInstance(component, Component)

    @given(subdir=..., file_name=...)
    def test_convert_multiple_components(
        self, subdir: Subdir, file_name: Literal["full.json", "minimal.json"]
    ):
        # grab a random test file and ensure it can be converted to msgspec definition
        full_path = TEST_FILES / subdir / file_name
        json_data = full_path.read_bytes()
        component_dicts: list[ComponentDict] = [json_decoder.decode(json_data)]

        components = convert_components(component_dicts)

        self.assertIsInstance(components, Sequence)
        self.assertIsInstance(components[0], Component)

    @given(subdir=..., file_name=...)
    def test_dump_to_builtins(
        self, subdir: Subdir, file_name: Literal["full.json", "minimal.json"]
    ):
        component = load_json(TEST_FILES / subdir / file_name)

        single_result = to_python(component)

        self.assertIsInstance(single_result, dict)
        self.assertIn("type", single_result)
        self.assertEqual(single_result["type"], component.type)

        multiple_results = to_python([component])

        self.assertIsInstance(multiple_results, list)
        self.assertEqual(multiple_results, [single_result])
