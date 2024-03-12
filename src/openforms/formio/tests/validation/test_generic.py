from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import validate_formio_data


class FallbackBehaviourTests(SimpleTestCase):

    def test_unknown_component_passthrough(self):
        # TODO: this should *not* pass when all components are implemented, it's a
        # temporary compatibility layer
        component: Component = {
            "type": "unknown-i-do-not-exist",
            "key": "foo",
            "label": "Fallback",
        }
        data: JSONValue = {"value": ["weird", {"data": "structure"}]}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)
