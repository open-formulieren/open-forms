from django.test import SimpleTestCase, tag

from hypothesis import example, given, strategies as st

from openforms.formio.tests.search_strategies import formio_key
from openforms.tests.search_strategies import json_primitives
from openforms.typing import JSONPrimitive

from ..datastructures import FormioConfig, FormioData
from ..typing import Component, FileComponent, SelectBoxesComponent
from ..visibility import is_hidden

SELECTBOXES: SelectBoxesComponent = {
    "type": "selectboxes",
    "key": "selectBoxes1",
    "label": "Select boxes",
    "values": [
        {"value": "a", "label": "A"},
        {"value": "b", "label": "B"},
    ],
}
FILE: FileComponent = {
    "type": "file",
    "key": "file1",
    "label": "File",
    "file": {"type": [], "allowedTypesLabels": []},
    "filePattern": "",
    "useConfigFiletypes": False,
    "storage": "url",
    "url": "",
}
FORMIO_COMPONENTS: list[Component] = [SELECTBOXES, FILE]


class IsHiddenTests(SimpleTestCase):
    def test_is_visible_in_frontend_with_selectboxes(self):
        data = FormioData({"selectBoxes1": {"a": True, "b": False}})

        component: Component = {
            "key": "textField1",
            "type": "textfield",
            "label": "Text field",
            "conditional": {"show": True, "when": "selectBoxes1", "eq": "a"},
        }
        formio_config = FormioConfig(
            name="test",
            components=[*FORMIO_COMPONENTS, component],
        )

        result = is_hidden(formio_config["textField1"], data, formio_config)

        self.assertFalse(result)

    def test_is_hidden_in_frontend_with_selectboxes(self):
        data = FormioData({"selectBoxes1": {"a": True, "b": False}})

        component: Component = {
            "key": "textField1",
            "type": "textfield",
            "label": "Text field",
            "conditional": {"show": False, "when": "selectBoxes1", "eq": "a"},
        }
        formio_config = FormioConfig(
            name="test",
            components=[*FORMIO_COMPONENTS, component],
        )

        result = is_hidden(formio_config["textField1"], data, formio_config)

        self.assertTrue(result)

    def test_is_hidden_if_not_selected(self):
        data = FormioData({"selectBoxes1": {"a": False, "b": False}})

        component: Component = {
            "key": "textField1",
            "type": "textfield",
            "label": "Text field",
            "conditional": {"show": True, "when": "selectBoxes1", "eq": "a"},
        }
        formio_config = FormioConfig(
            name="test",
            components=[*FORMIO_COMPONENTS, component],
        )

        result = is_hidden(formio_config["textField1"], data, formio_config)

        self.assertTrue(result)

    def test_is_visible_if_not_selected(self):
        data = FormioData({"selectBoxes1": {"a": False, "b": False}})

        component: Component = {
            "key": "textField1",
            "type": "textfield",
            "label": "Text field",
            "conditional": {"show": False, "when": "selectBoxes1", "eq": "a"},
        }
        formio_config = FormioConfig(
            name="test",
            components=[*FORMIO_COMPONENTS, component],
        )

        result = is_hidden(formio_config["textField1"], data, formio_config)

        self.assertFalse(result)

    @tag("gh-6181")
    def test_is_hidden_in_frontend_with_file(self):
        data = FormioData({"file1": []})

        component: Component = {
            "type": "textfield",
            "key": "textField1",
            "label": "textfield",
            "conditional": {
                "show": False,
                "when": "file1",
                "eq": "",  # should be [], but formio-builder/formio legacy use strings...
            },
        }
        formio_config = FormioConfig(
            name="test",
            components=[*FORMIO_COMPONENTS, component],
        )

        result = is_hidden(formio_config["textField1"], data, formio_config)

        self.assertTrue(result)

    @given(
        hidden=st.booleans(),
        show=st.one_of(st.none(), st.booleans(), st.just("")),
        when=st.one_of(st.none(), formio_key(), st.just("")),
        eq=json_primitives(),
    )
    # Sentry 326223
    @example(hidden=True, show="", when=None, eq="")
    def test_conditional_resiliency(
        self,
        hidden: bool,
        show: None | bool | str,
        when: None | str,
        eq: JSONPrimitive,
    ):
        data = FormioData()
        component: Component = {
            "key": "someComponent",
            "type": "textfield",
            "label": "Dummy",
            "multiple": False,
            "hidden": hidden,
            "defaultValue": "",
            "prefill": {"plugin": "", "attribute": ""},
            "conditional": {
                # deliberate wrong type to test resiliency
                "show": show,  # pyright: ignore[reportAssignmentType]
                "when": when,
                "eq": eq,
            },
        }
        formio_config = FormioConfig(
            name="test",
            components=[*FORMIO_COMPONENTS, component],
        )

        try:
            is_hidden(formio_config["someComponent"], data, formio_config)
        except Exception:
            self.fail("Visibility check unexpectedly crashed")
