from django.test import RequestFactory, TestCase

from hypothesis import given
from hypothesis.extra.django import TestCase as HypothesisTestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.api.datastructures import FormVariableWrapper
from openforms.forms.api.serializers import FormSerializer
from openforms.forms.api.serializers.logic.action_serializers import (
    LogicComponentActionSerializer,
)
from openforms.forms.tests.factories import (
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
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


class FormSerializerTest(TestCase):
    def test_form_with_cosign(self):
        form_step = FormStepFactory.create(
            form__slug="form-with-cosign",
            form_definition__configuration={
                "components": [
                    {
                        "key": "cosignField",
                        "label": "Cosign",
                        "type": "cosign",
                        "authPlugin": "digid",
                    }
                ]
            },
        )

        factory = RequestFactory()
        request = factory.get("/foo")
        request.user = UserFactory.create()

        serializer = FormSerializer(
            instance=form_step.form, context={"request": request}
        )
        cosign_login_info = serializer.data["cosign_login_info"]

        self.assertIsNotNone(cosign_login_info)

    def test_form_without_cosign(self):
        form_step = FormStepFactory.create(
            form__slug="form-without-cosign",
            form_definition__configuration={
                "components": [
                    {
                        "key": "notCosign",
                        "label": "Not Cosign",
                        "type": "textfield",
                    }
                ]
            },
        )

        factory = RequestFactory()
        request = factory.get("/foo")
        request.user = UserFactory.create()

        serializer = FormSerializer(
            instance=form_step.form, context={"request": request}
        )
        cosign_login_info = serializer.data["cosign_login_info"]

        self.assertIsNone(cosign_login_info)
