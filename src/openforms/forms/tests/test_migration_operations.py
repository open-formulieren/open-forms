from contextlib import contextmanager
from unittest.mock import patch

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from openforms.formio.migration_converters import ComponentConverter
from openforms.formio.typing import Component

from ..migration_operations import ApplyConverter, ConvertComponentsOperation
from ..models import FormDefinition
from .factories import FormDefinitionFactory


@contextmanager
def mock_component_converters(replacement: dict[str, dict[str, ComponentConverter]]):
    with patch("openforms.forms.migration_operations.CONVERTERS", new=replacement):
        yield


def noop(component: Component):
    return False


def add_foo_property(component: Component):
    component["foo"] = "bar"  # type: ignore
    return True


class ConvertComponentsOperationTests(TestCase):
    @mock_component_converters({})
    def test_unknown_component_type(self):
        with self.assertRaises(ImproperlyConfigured):
            ConvertComponentsOperation("textfield", "dummy")

    @mock_component_converters({"textfield": {}})
    def test_unknown_conversion_identifier(self):
        with self.assertRaises(ImproperlyConfigured):
            ConvertComponentsOperation("textfield", "dummy")

    @mock_component_converters({"textfield": {"noop": noop}})
    def test_no_modifications(self):
        FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "Text",
                    }
                ]
            }
        )

        apply_converter = ApplyConverter("textfield", "noop")

        # we only expect the query to loop over all FDs
        with self.assertNumQueries(1):
            apply_converter(apps, None)

    @mock_component_converters({"textfield": {"add_foo": add_foo_property}})
    def test_targets_only_specified_component_type(self):
        FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "Text",
                    },
                    {
                        "type": "nottextfield",
                        "key": "textfield",
                        "label": "Text",
                    },
                ]
            }
        )

        apply_converter = ApplyConverter("textfield", "add_foo")

        # 1. loop over all form definitions
        # 2. one (bulk) update query
        with self.assertNumQueries(2):
            apply_converter(apps, None)

        fd = FormDefinition.objects.get()
        comp1, comp2 = fd.configuration["components"]

        with self.subTest("updated component"):
            self.assertIn("foo", comp1)

        with self.subTest("ignored component"):
            self.assertNotIn("foo", comp2)
