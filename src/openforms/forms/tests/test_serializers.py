from django.test import TestCase

from hypothesis import given
from hypothesis.extra.django import TestCase as HypothesisTestCase

from openforms.forms.api.datastructures import FormVariableWrapper
from openforms.forms.api.serializers.logic.action_serializers import (
    LogicComponentActionSerializer,
)
from openforms.forms.tests.factories import FormFactory, FormVariableFactory
from openforms.tests.search_strategies import json_primitives
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources


class LogicComponentActionSerializerPropertyTest(HypothesisTestCase):
    @given(json_primitives())
    def test_date_format_validation_against_primitive_json_values(self, json_value):
        """Assert that serializer is invalid for random Primitive json data types
        (str, int, etc.) as logic action values for date variables
        """
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="date_var",
            form=form,
            data_type=FormVariableDataTypes.date,
        )
        form_vars = FormVariableWrapper(form=form)

        serializer = LogicComponentActionSerializer(
            data={
                "variable": "date_var",
                "action": {
                    "type": "variable",
                    "value": json_value,
                },
            },
            context={"request": None, "form_variables": form_vars},
        )
        self.assertFalse(serializer.is_valid())


class LogicComponentActionSerializerTest(TestCase):
    def test_date_variable_with_non_trivial_json_trigger(self):
        """Check that valid JSON expressions are not ruled out by date format validation"""
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="someDate",
            form=form,
            data_type=FormVariableDataTypes.date,
        )
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="anotherDate",
            form=form,
            data_type=FormVariableDataTypes.date,
        )
        form_vars = FormVariableWrapper(form=form)

        serializer = LogicComponentActionSerializer(
            data={
                "json_logic_trigger": {
                    "==": [
                        {"var": "someDate"},
                        {},
                    ]
                },
                "variable": "anotherDate",
                "action": {
                    "type": "variable",
                    "value": {"var": "anotherDate"},
                },
            },
            context={"request": None, "form_variables": form_vars},
        )

        self.assertTrue(serializer.is_valid())
