from django.test import SimpleTestCase

from hypothesis import example, given, strategies as st

from openforms.formio.tests.search_strategies import formio_key
from openforms.tests.search_strategies import json_primitives
from openforms.typing import JSONPrimitive

from ..typing import Component
from ..utils import is_visible_in_frontend


class FormioUtilsTest(SimpleTestCase):
    def test_is_visible_in_frontend_with_selectboxes(self):
        data = {"selectBoxes1": {"a": True, "b": False}}

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": True, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertTrue(result)

    def test_is_hidden_in_frontend_with_selectboxes(self):
        data = {"selectBoxes1": {"a": True, "b": False}}

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": False, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertFalse(result)

    def test_is_hidden_if_not_selected(self):
        data = {"selectBoxes1": {"a": False, "b": False}}

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": True, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertFalse(result)

    def test_is_visible_if_not_selected(self):
        data = {"selectBoxes1": {"a": False, "b": False}}

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
        data = {}
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
