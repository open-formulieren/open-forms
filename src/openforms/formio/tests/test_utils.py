from django.test import SimpleTestCase

from hypothesis import example, given, strategies as st

from openforms.formio.tests.search_strategies import formio_key
from openforms.tests.search_strategies import json_primitives
from openforms.typing import JSONPrimitive

from ..datastructures import FormioData
from ..typing import Component, SelectBoxesComponent
from ..utils import get_component_empty_value, is_visible_in_frontend


class FormioUtilsTest(SimpleTestCase):
    def test_is_visible_in_frontend_with_selectboxes(self):
        data = FormioData({"selectBoxes1": {"a": True, "b": False}})

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": True, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertTrue(result)

    def test_is_hidden_in_frontend_with_selectboxes(self):
        data = FormioData({"selectBoxes1": {"a": True, "b": False}})

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": False, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertFalse(result)

    def test_is_hidden_if_not_selected(self):
        data = FormioData({"selectBoxes1": {"a": False, "b": False}})

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": True, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertFalse(result)

    def test_is_visible_if_not_selected(self):
        data = FormioData({"selectBoxes1": {"a": False, "b": False}})

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": False, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

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
                "show": show,
                "when": when,
                "eq": eq,
            },
        }

        try:
            is_visible_in_frontend(component, data)
        except Exception:
            self.fail("Visibility check unexpectedly crashed")


class GetComponentEmptyValueTests(SimpleTestCase):
    def test_selectboxes_default_value(self):
        component: SelectBoxesComponent = {
            "key": "selectboxes",
            "type": "selectboxes",
            "label": "Select Boxes",
            "values": [
                {"label": "a", "value": "a"},
                {"label": "b", "value": "b"},
                {"label": "c", "value": "c"},
            ],
            "defaultValue": {"a": False, "b": False, "c": False},
        }

        empty_value = get_component_empty_value(component)
        self.assertEqual(empty_value, {"a": False, "b": False, "c": False})

    def test_selectboxes_configuration_updated_and_no_default_value(self):
        # This is the situation when the data source is another variable or reference
        # lists, AND the configuration was dynamically updated
        component: SelectBoxesComponent = {
            "key": "selectboxes",
            "type": "selectboxes",
            "label": "Select Boxes",
            "values": [
                {"label": "a", "value": "a"},
                {"label": "b", "value": "b"},
                {"label": "c", "value": "c"},
            ],
            "defaultValue": {},
        }

        empty_value = get_component_empty_value(component)
        self.assertEqual(empty_value, {"a": False, "b": False, "c": False})

    def test_selectboxes_configruation_not_updated_and_no_default_value(self):
        # If the configuration was not updated, the 'values' list has one entry with
        # the 'label' and 'value' an empty string.
        component: SelectBoxesComponent = {
            "key": "selectboxes",
            "type": "selectboxes",
            "label": "Select Boxes",
            "values": [
                {"label": "", "value": ""},
            ],
        }

        empty_value = get_component_empty_value(component)
        self.assertEqual(empty_value, {})
