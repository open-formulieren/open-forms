from glom import GlomError, glom

from openforms.typing import JSONObject, JSONValue

from ..typing import Component
from ..utils import iter_components


def _get_component(configuration: JSONObject, key: str) -> Component | None:
    for component in iter_components(configuration=configuration, recursive=True):
        if component["key"] == key:
            return component


class FormioMixin:
    def assertFormioComponent(
        self, configuration: JSONObject, key: str, properties_map: dict[str, JSONValue]
    ) -> None:
        """
        Assert that the formio component with specified key has the expected properties.

        :arg configuration: Formio form configuration
        :arg key: the unique key of the component to check
        :arg properties_map: a mapping of formio property name to expected property
          value. Note that the dict keys can be dotted paths for nested properties.
        """
        component = _get_component(configuration, key)
        if component is None:
            self.fail(f"Component with key '{key}' not found in configuration.")

        for key, expected_value in properties_map.items():
            with self.subTest(property=key, expected=expected_value):
                try:
                    value = glom(component, key)
                except GlomError:
                    self.fail(f"Could not find property with path '{key}' in component")
                self.assertEqual(value, expected_value)
