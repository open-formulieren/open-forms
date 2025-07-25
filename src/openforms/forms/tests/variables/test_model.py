import timeit
import unittest
from contextlib import contextmanager

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, tag

from openforms.prefill.constants import IdentifierRoles
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ...models import FormDefinition, FormStep, FormVariable
from ..factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)


@contextmanager
def assert_execution_time(test_case: unittest.TestCase, *, seconds: int | float):
    start_time = timeit.default_timer()
    yield
    # in fractional seconds
    execution_time = timeit.default_timer() - start_time
    test_case.assertLess(
        execution_time,
        seconds,
        f"Execution took too long: {execution_time:.2f}s",
    )


class FormVariableModelTests(TestCase):
    # valid cases (constraint: prefill_config_component_or_user_defined)
    def test_prefill_plugin_prefill_attribute_prefill_options_empty(self):
        # user defined
        FormVariableFactory.create(
            prefill_plugin="",
            prefill_attribute="",
            prefill_options={},
        )
        # component
        FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test-key",
                        "label": "Test label",
                        "prefill": {"plugin": "", "attribute": ""},
                    }
                ]
            }
        )

    def test_prefill_options_empty(self):
        FormVariableFactory.create(
            prefill_plugin="demo",
            prefill_attribute="demo",
            prefill_options={},
        )

    def test_prefill_attribute_empty(self):
        FormVariableFactory.create(
            prefill_plugin="demo",
            prefill_attribute="",
            prefill_options={"variables_mapping": [{"variable_key": "data"}]},
        )

    # invalid cases (constraint: prefill_config_component_or_user_defined)
    def test_prefill_plugin_prefill_attribute_empty(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                prefill_plugin="",
                prefill_attribute="",
                prefill_options={"variables_mapping": [{"variable_key": "data"}]},
            )

    def test_prefill_plugin_prefill_options_empty(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                prefill_plugin="",
                prefill_attribute="demo",
                prefill_options={},
            )

    def test_prefill_plugin_prefill_attribute_prefill_options_not_empty(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                prefill_plugin="demo",
                prefill_attribute="demo",
                prefill_options={"variables_mapping": [{"variable_key": "data"}]},
            )

    def test_prefill_attribute_prefill_options_empty(self):
        with self.assertRaises(IntegrityError):
            FormStepFactory.create(
                form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "test-key",
                            "label": "Test label",
                            "prefill": {"plugin": "demo", "attribute": ""},
                        }
                    ]
                }
            )

    def test_valid_prefill_plugin_config(self):
        try:
            FormVariableFactory.create(prefill_plugin="demo", prefill_attribute="demo")
        except (ValidationError, IntegrityError) as e:
            raise self.failureException("Failed valid input") from e

    def test_service_fetch_config_and_prefill_plugin_are_mutually_exclusive(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                service_fetch_configuration=ServiceFetchConfigurationFactory.create(),
                prefill_plugin="demo",
                prefill_attribute="demo",
            )

    def test_component_variable_without_form_definition_invalid(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                source=FormVariableSources.component, form_definition=None
            )

    def test_variable_can_have_a_service_fetch_configuration(self):
        try:
            FormVariableFactory.create(
                service_fetch_configuration=ServiceFetchConfigurationFactory.create()
            )
        except TypeError as e:
            raise self.failureException("Failed valid input") from e

    def test_component_variable_data_type_automatically_set(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [{"type": "textfield", "key": "test"}]
            },
        )

        variable = form.formvariable_set.get(key="test")

        self.assertEqual("string", variable.data_type)

    def test_component_variable_initial_value_automatically_set(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test1",
                        "defaultValue": "test default",
                    },
                    {"type": "textfield", "key": "test2"},
                    {"type": "textfield", "key": "test3", "defaultValue": None},
                ]
            },
        )

        variable1 = form.formvariable_set.get(key="test1")
        variable2 = form.formvariable_set.get(key="test2")
        variable3 = form.formvariable_set.get(key="test3")

        self.assertEqual("test default", variable1.initial_value)
        self.assertIsNone(variable2.initial_value)
        self.assertIsNone(variable3.initial_value)

    def test_set_variable_info_with_multiple(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test1",
                        "multiple": True,
                        "defaultValue": ["test default"],
                    },
                    {
                        "type": "textfield",
                        "key": "test2",
                        "multiple": True,
                    },
                    {
                        "type": "textfield",
                        "key": "test3",
                        "multiple": True,
                        "defaultValue": None,
                    },
                ]
            },
        )

        variable1 = form.formvariable_set.get(key="test1")
        variable2 = form.formvariable_set.get(key="test2")
        variable3 = form.formvariable_set.get(key="test3")

        self.assertEqual(["test default"], variable1.initial_value)
        self.assertEqual([], variable2.initial_value)
        self.assertEqual([], variable3.initial_value)
        self.assertEqual(FormVariableDataTypes.array, variable1.data_type)
        self.assertEqual(FormVariableDataTypes.array, variable2.data_type)
        self.assertEqual(FormVariableDataTypes.array, variable3.data_type)

    def test_variable_with_array_default_value(self):
        variable = FormVariableFactory.create(
            data_type=FormVariableDataTypes.array, initial_value=[]
        )

        self.assertEqual([], variable.get_initial_value())

    def test_user_defined_variables_cast_initial_value(self):
        values_to_try = {
            FormVariableDataTypes.string: ["", "Some value"],
            FormVariableDataTypes.boolean: ["", False, True, None],
            FormVariableDataTypes.object: ["", {}, {"some": "object"}],
            FormVariableDataTypes.array: ["", "Test", [], ["another", "test"]],
            FormVariableDataTypes.int: [None, "", 1.1, 1.0, 1],
            FormVariableDataTypes.float: [None, "", 1.4],
            FormVariableDataTypes.datetime: [
                "",
                "Invalid datetime",
                "2022-09-05",
                "2022-09-08T00:00:00+02:00",
            ],
            FormVariableDataTypes.time: [
                "",
                "invalid time",
                "11:30",
                "11:30:00",
                "2022-09-08T11:30:00+02:00",
            ],
            FormVariableDataTypes.date: [
                "",
                "Invalid date",
                "2022-09-05",
                "2022-09-08T00:00:00+02:00",
            ],
        }

        expected_values = {
            FormVariableDataTypes.string: ["", "Some value"],
            FormVariableDataTypes.boolean: [False, False, True, False],
            FormVariableDataTypes.object: [{}, {}, {"some": "object"}],
            FormVariableDataTypes.array: [
                [],
                ["T", "e", "s", "t"],
                [],
                ["another", "test"],
            ],
            FormVariableDataTypes.int: [None, None, 1, 1, 1],
            FormVariableDataTypes.float: [None, None, 1.4],
            FormVariableDataTypes.datetime: [
                "",
                "",
                "2022-09-05",
                "2022-09-08T00:00:00+02:00",
            ],
            FormVariableDataTypes.time: [
                "",
                "",
                "11:30",
                "11:30:00",
                "2022-09-08T11:30:00+02:00",
            ],
            FormVariableDataTypes.date: [
                "",
                "",
                "2022-09-05",
                "2022-09-08T00:00:00+02:00",
            ],
        }

        for data_type, data_type_label in FormVariableDataTypes.choices:
            if data_type == FormVariableDataTypes.partners:
                # Not useful to test anything for this data type, as it is only used as
                # a subtype. The data type of the partners component is still an array.
                continue

            for index, initial_value in enumerate(values_to_try[data_type]):
                with self.subTest(
                    f"Data type: {data_type_label}, initial value: {initial_value}"
                ):
                    variable = FormVariableFactory.create(
                        user_defined=True,
                        initial_value=initial_value,
                        data_type=data_type,
                    )

                    self.assertEqual(
                        expected_values[data_type][index], variable.initial_value
                    )


class FormVariableManagerTests(TestCase):
    @tag("gh-5084", "slow")
    def test_performance_upsert_single_form_definition(self):
        many_components = [
            {
                "type": "textfield",
                "key": f"component-{i}",
                "label": f"Field {i}",
                "id": f"comp{i}",
                "prefill": {
                    "plugin": "demo",
                    "attribute": "random",
                    "identifierRole": IdentifierRoles.main,
                },
            }
            for i in range(1000)
        ]
        fd = FormDefinition.objects.create(
            slug="slak",
            configuration={"components": many_components},
            is_reusable=False,
        )
        form = FormFactory.create()
        FormStep.objects.create(form=form, form_definition=fd, order=0, slug="slak")
        assert not FormVariable.objects.exists()

        with (
            self.subTest("initial inserts"),
            # 5 seconds is giving *a lot* of credit, but before the performance patch
            # this was taking 10+ seconds. In isolation, this takes 100-400ms.
            assert_execution_time(self, seconds=5),
        ):
            FormVariable.objects.synchronize_for(fd)

        self.assertEqual(FormVariable.objects.count(), 1000)  # 1000 records created

        with (
            self.subTest("re-sync"),
            # this should not take any time at all because no database IO is expected
            # since nothing changed
            assert_execution_time(self, seconds=2),
        ):
            FormVariable.objects.synchronize_for(fd)

        # no new records created
        self.assertEqual(FormVariable.objects.count(), 1000)

    @tag("gh-5084", "slow")
    def test_performance_upsert_reusable_form_definition(self):
        many_components = [
            {
                "type": "textfield",
                "key": f"component-{i}",
                "label": f"Field {i}",
                "id": f"comp{i}",
            }
            for i in range(100)
        ]
        fd = FormDefinition.objects.create(
            slug="slak",
            configuration={"components": many_components},
            is_reusable=True,
        )
        forms = FormFactory.create_batch(10)
        for form in forms:
            FormStep.objects.create(form=form, form_definition=fd, order=0, slug="slak")
        assert not FormVariable.objects.exists()

        with (
            self.subTest("initial inserts"),
            # it's mostly the number of components that causes performance issues, not
            # necessarily the number of forms that use the form definition
            assert_execution_time(self, seconds=3),
        ):
            FormVariable.objects.synchronize_for(fd)

        self.assertEqual(FormVariable.objects.count(), 1000)  # 1000 records created

        with self.subTest("update some components"):
            # remove 10
            fd.configuration["components"] = fd.configuration["components"][:90]
            # update 10
            for i in range(10, 20):
                fd.configuration["components"][i]["label"] = f"Updated field {i}"
            # insert 10 new ones
            for i in range(0, 10):
                fd.configuration["components"].append(
                    {
                        "type": "textfield",
                        "key": f"new-component-{i}",
                        "label": f"New field {i}",
                        "id": f"newComp{i}",
                    }
                )
            fd.save()

            with (
                self.subTest("initial inserts"),
                # it's mostly the number of components that causes performance issues, not
                # necessarily the number of forms that use the form definition
                assert_execution_time(self, seconds=3),
            ):
                FormVariable.objects.synchronize_for(fd)

            self.assertEqual(
                FormVariable.objects.count(), 1000
            )  # 1000 records still exist
            self.assertEqual(FormVariable.objects.filter(key="component-5").count(), 10)
            self.assertFalse(FormVariable.objects.filter(key="component-95").exists())
            fv_14 = FormVariable.objects.filter(key="component-14").order_by("?")[0]
            self.assertEqual(fv_14.name, "Updated field 14")

    def test_synchronize_for_correctness(self):
        """
        Assert that creating form variables from a FD produces correct results.

        We have some risky performance-critical code in synchronize_for that can
        possibly lead to wrong result if held the wrong way. This test tries to prevent
        such mistakes.
        """
        fd = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "date",
                        "key": "aDate",
                        "label": "A date",
                        "prefill": {
                            "plugin": "aPlugin",
                            "attribute": "anAttribute",
                        },
                        "defaultValue": "2025-01-01",
                        "isSensitiveData": True,
                    },
                    {
                        "type": "selectboxes",
                        "key": "aSelectboxes",
                        "values": [{"value": "foo", "label": "Foo"}],
                        "label": "Some selectboxes",
                        "defaultValue": {"foo": True},
                    },
                ]
            }
        )
        step1 = FormStepFactory.create(form_definition=fd)
        step2 = FormStepFactory.create(form_definition=fd)
        assert step1.form != step2.form

        with self.subTest("assert creation"):
            # the factory already implicitly calls the synchronize_for, but let's make it
            # super explicit
            FormVariable.objects.synchronize_for(fd)

            form_variables = FormVariable.objects.all()
            self.assertEqual(len(form_variables), 2 + 2)  # 2 for each form (step)
            step1_variables = {
                variable.key: variable
                for variable in form_variables
                if variable.form == step1.form
            }
            step2_variables = {
                variable.key: variable
                for variable in form_variables
                if variable.form == step1.form
            }
            self.assertEqual(step1_variables.keys(), step2_variables.keys())

            for container in (step1_variables, step2_variables):
                with self.subTest("date variable"):
                    date_variable = container["aDate"]
                    self.assertEqual(date_variable.form_definition, fd)
                    self.assertEqual(date_variable.name, "A date")
                    self.assertEqual(
                        date_variable.source, FormVariableSources.component
                    )
                    self.assertIsNone(date_variable.service_fetch_configuration)
                    self.assertEqual(date_variable.prefill_plugin, "aPlugin")
                    self.assertEqual(date_variable.prefill_attribute, "anAttribute")
                    self.assertEqual(
                        date_variable.prefill_identifier_role, IdentifierRoles.main
                    )
                    self.assertEqual(date_variable.prefill_options, {})
                    self.assertEqual(
                        date_variable.data_type, FormVariableDataTypes.date
                    )
                    self.assertEqual(date_variable.data_format, "")
                    self.assertTrue(date_variable.is_sensitive_data)
                    self.assertEqual(date_variable.initial_value, "2025-01-01")

                with self.subTest("selectboxes variable"):
                    date_variable = container["aSelectboxes"]
                    self.assertEqual(date_variable.form_definition, fd)
                    self.assertEqual(date_variable.name, "Some selectboxes")
                    self.assertEqual(
                        date_variable.source, FormVariableSources.component
                    )
                    self.assertIsNone(date_variable.service_fetch_configuration)
                    self.assertEqual(date_variable.prefill_plugin, "")
                    self.assertEqual(date_variable.prefill_attribute, "")
                    self.assertEqual(
                        date_variable.prefill_identifier_role, IdentifierRoles.main
                    )
                    self.assertEqual(date_variable.prefill_options, {})
                    self.assertEqual(
                        date_variable.data_type, FormVariableDataTypes.object
                    )
                    self.assertEqual(date_variable.data_format, "")
                    self.assertFalse(date_variable.is_sensitive_data)
                    self.assertEqual(date_variable.initial_value, {"foo": True})

        # update some components, remove one and add a new one
        with self.subTest("update form definition"):
            fd.configuration = {
                "components": [
                    # updated
                    {
                        "type": "number",
                        "key": "aDate",
                        "label": "Changed name",
                        "defaultValue": 42,
                    },
                    # replaces selectboxes
                    {
                        "type": "editgrid",
                        "key": "repeatingGroup",
                        "label": "A repeating group",
                        "components": [
                            {
                                "type": "selectboxes",
                                "key": "aSelectboxes",
                                "values": [{"value": "foo", "label": "Foo"}],
                                "label": "Some selectboxes",
                                "defaultValue": {"foo": True},
                            },
                        ],
                    },
                ]
            }
            fd.save()

            FormVariable.objects.synchronize_for(fd)

            form_variables = FormVariable.objects.all()
            self.assertEqual(len(form_variables), 2 + 2)  # 2 for each form (step)
            step1_variables = {
                variable.key: variable
                for variable in form_variables
                if variable.form == step1.form
            }
            step2_variables = {
                variable.key: variable
                for variable in form_variables
                if variable.form == step1.form
            }
            self.assertEqual(step1_variables.keys(), step2_variables.keys())
            for container in (step1_variables, step2_variables):
                with self.subTest("'date' variable"):
                    date_variable = container["aDate"]
                    self.assertEqual(date_variable.form_definition, fd)
                    self.assertEqual(date_variable.name, "Changed name")
                    self.assertEqual(
                        date_variable.source, FormVariableSources.component
                    )
                    self.assertIsNone(date_variable.service_fetch_configuration)
                    self.assertEqual(date_variable.prefill_plugin, "")
                    self.assertEqual(date_variable.prefill_attribute, "")
                    self.assertEqual(
                        date_variable.prefill_identifier_role, IdentifierRoles.main
                    )
                    self.assertEqual(date_variable.prefill_options, {})
                    self.assertEqual(
                        date_variable.data_type, FormVariableDataTypes.float
                    )
                    self.assertEqual(date_variable.data_format, "")
                    self.assertFalse(date_variable.is_sensitive_data)
                    self.assertEqual(date_variable.initial_value, 42)

                with self.subTest("editgrid variable"):
                    date_variable = container["repeatingGroup"]
                    self.assertEqual(date_variable.form_definition, fd)
                    self.assertEqual(date_variable.name, "A repeating group")
                    self.assertEqual(
                        date_variable.source, FormVariableSources.component
                    )
                    self.assertIsNone(date_variable.service_fetch_configuration)
                    self.assertEqual(date_variable.prefill_plugin, "")
                    self.assertEqual(date_variable.prefill_attribute, "")
                    self.assertEqual(
                        date_variable.prefill_identifier_role, IdentifierRoles.main
                    )
                    self.assertEqual(date_variable.prefill_options, {})
                    self.assertEqual(
                        date_variable.data_type, FormVariableDataTypes.array
                    )
                    self.assertEqual(date_variable.data_format, "")
                    self.assertFalse(date_variable.is_sensitive_data)
                    self.assertIsNone(date_variable.initial_value)
