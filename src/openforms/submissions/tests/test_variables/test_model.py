from datetime import date, datetime, time

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from openforms.formio.service import FormioData
from openforms.forms.tests.factories import (
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableDataTypes

from ...models import SubmissionValueVariable
from ..factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)


class SubmissionValueVariableModelTests(TestCase):
    def test_unique_together_submission_key(self):
        variable1 = SubmissionValueVariableFactory.create(key="var1")

        with self.assertRaises(IntegrityError):
            SubmissionValueVariable.objects.create(
                submission=variable1.submission, key="var1"
            )

    def test_can_create_instances(self):
        SubmissionValueVariableFactory.create()
        SubmissionValueVariableFactory.create()

    def test_to_python(self):
        """
        Test that the serialized value can be converted to native python objects.
        """
        with self.subTest("string"):
            string_var = SubmissionValueVariableFactory.create(
                value="a string",
                data_type=FormVariableDataTypes.string,
                form_variable__user_defined=True,
            )

            string_value = string_var.to_python()

            self.assertEqual(string_value, "a string")

        with self.subTest("boolean"):
            bool_var = SubmissionValueVariableFactory.create(
                value=True,
                data_type=FormVariableDataTypes.boolean,
                form_variable__user_defined=True,
            )

            bool_value = bool_var.to_python()

            self.assertIs(bool_value, True)

        with self.subTest("object"):
            object_var = SubmissionValueVariableFactory.create(
                value={"foo": "bar"},
                data_type=FormVariableDataTypes.object,
                form_variable__user_defined=True,
            )

            object_value = object_var.to_python()

            self.assertIsInstance(object_value, dict)

        with self.subTest("array"):
            array_var = SubmissionValueVariableFactory.create(
                value=[1, 2, "foo"],
                data_type=FormVariableDataTypes.array,
                form_variable__user_defined=True,
            )

            array_value = array_var.to_python()

            self.assertIsInstance(array_value, list)

        with self.subTest("int"):
            int_var = SubmissionValueVariableFactory.create(
                value=42,
                data_type=FormVariableDataTypes.int,
                form_variable__user_defined=True,
            )

            int_value = int_var.to_python()

            self.assertEqual(int_value, 42)

        with self.subTest("float"):
            float_var = SubmissionValueVariableFactory.create(
                value=4.20,
                data_type=FormVariableDataTypes.float,
                form_variable__user_defined=True,
            )

            float_value = float_var.to_python()

            self.assertEqual(float_value, 4.20)

        # Dates submitted by the SDK have the time part stripped off
        # User defined variables of type date also don't have the time part
        with self.subTest("date 1"):
            date_var1 = SubmissionValueVariableFactory.create(
                value="2022-09-13",
                data_type=FormVariableDataTypes.date,
                form_variable__user_defined=True,
            )

            date_value1 = date_var1.to_python()

            self.assertIsInstance(date_value1, date)
            # datetimes must be made aware in our local timezone
            self.assertEqual(
                date_value1,
                date(2022, 9, 13),
            )

        with self.subTest("date multiple"):
            date_var_multiple = SubmissionValueVariableFactory.create(
                key="dateVarMultiple",
                value=["2025-07-15", "2025-07-16"],
                data_type=FormVariableDataTypes.array,
                data_subtype=FormVariableDataTypes.date,
            )

            date_value_multiple = date_var_multiple.to_python()
            self.assertEqual(
                date_value_multiple, [date(2025, 7, 15), date(2025, 7, 16)]
            )

        with self.subTest("date empty"):
            date_var_empty = SubmissionValueVariableFactory.create(
                value="",
                data_type=FormVariableDataTypes.date,
            )

            self.assertIsNone(date_var_empty.to_python())

        with self.subTest("datetime 1"):
            date_var3 = SubmissionValueVariableFactory.create(
                value="2022-09-13T11:10:45+02:00",
                data_type=FormVariableDataTypes.datetime,
                form_variable__user_defined=True,
            )

            date_value3 = date_var3.to_python()

            self.assertIsInstance(date_value3, datetime)
            # datetimes must be made aware in our local timezone
            self.assertIsNotNone(date_value3.tzinfo)
            expected = timezone.make_aware(datetime(2022, 9, 13, 11, 10, 45))
            self.assertEqual(date_value3, expected)

        with self.subTest("datetime 2 (naive datetime)"):
            date_var4 = SubmissionValueVariableFactory.create(
                value="2022-09-13T11:10:45",
                data_type=FormVariableDataTypes.datetime,
                form_variable__user_defined=True,
            )

            date_value4 = date_var4.to_python()

            self.assertIsInstance(date_value4, datetime)
            # datetimes must be made aware in our local timezone
            self.assertIsNotNone(date_value4.tzinfo)
            expected = timezone.make_aware(datetime(2022, 9, 13, 11, 10, 45))
            self.assertEqual(date_value4, expected)

        with self.subTest("datetime multiple"):
            datetime_var_multiple = SubmissionValueVariableFactory.create(
                key="datetimeVarMultiple",
                value=["2025-07-15T12:34:56", "2025-07-16:11:22:33"],
                data_type=FormVariableDataTypes.array,
                data_subtype=FormVariableDataTypes.datetime,
            )

            datetime_value_multiple = datetime_var_multiple.to_python()
            self.assertEqual(
                datetime_value_multiple,
                [
                    timezone.make_aware(datetime(2025, 7, 15, 12, 34, 56)),
                    timezone.make_aware(datetime(2025, 7, 16, 11, 22, 33)),
                ],
            )

        with self.subTest("datetime empty"):
            datetime_var_empty = SubmissionValueVariableFactory.create(
                value="",
                data_type=FormVariableDataTypes.datetime,
            )

            self.assertIsNone(datetime_var_empty.to_python())

        with self.subTest("time"):
            time_var = SubmissionValueVariableFactory.create(
                value="11:15",
                data_type=FormVariableDataTypes.time,
                form_variable__user_defined=True,
            )

            time_value = time_var.to_python()

            # django does not seem to be able to make a time object tz-aware 🤔
            # we'll see if that causes any issues
            self.assertEqual(time_value, time(11, 15))

        with self.subTest("Invalid time"):
            # Issue 3647
            time_var = SubmissionValueVariableFactory.create(
                value="Invalid date",
                data_type=FormVariableDataTypes.time,
                form_variable__user_defined=True,
            )

            time_value = time_var.to_python()

            self.assertIsNone(time_value)

        with self.subTest("Native time object"):
            time_var = SubmissionValueVariableFactory.create(
                value="11:15",
                data_type=FormVariableDataTypes.time,
                form_variable__user_defined=True,
            )

            time_value = time_var.to_python(time(9, 41))
            self.assertEqual(time_value, time(9, 41))

        with self.subTest("time multiple"):
            time_var_multiple = SubmissionValueVariableFactory.create(
                key="timeVarMultiple",
                value=["12:34", "20:42"],
                data_type=FormVariableDataTypes.array,
                data_subtype=FormVariableDataTypes.time,
            )

            time_value_multiple = time_var_multiple.to_python()
            self.assertEqual(time_value_multiple, [time(12, 34), time(20, 42)])

        with self.subTest("time empty"):
            time_var_empty = SubmissionValueVariableFactory.create(
                value="",
                data_type=FormVariableDataTypes.time,
            )

            self.assertIsNone(time_var_empty.to_python())

        with self.subTest("partners"):
            partners_var = SubmissionValueVariableFactory.create(
                key="partners",
                value=[
                    {
                        "bsn": "111222333",
                        "initials": "F. O. O.",
                        "affixes": "",
                        "lastName": "Bar",
                        "dateOfBirth": "2000-01-01",
                    }
                ],
                data_type=FormVariableDataTypes.array,
                data_subtype=FormVariableDataTypes.partners,
            )

            partners_value = partners_var.to_python()
            self.assertEqual(
                partners_value,
                [
                    {
                        "bsn": "111222333",
                        "initials": "F. O. O.",
                        "affixes": "",
                        "lastName": "Bar",
                        "dateOfBirth": date(2000, 1, 1),
                    }
                ],
            )

        with self.subTest("children"):
            children_var = SubmissionValueVariableFactory.create(
                key="children",
                value=[
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                    },
                ],
                data_type=FormVariableDataTypes.array,
                data_subtype=FormVariableDataTypes.children,
            )

            children_value = children_var.to_python()
            self.assertEqual(
                children_value,
                [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": date(2023, 2, 1),
                        "dateOfBirthPrecision": "date",
                    }
                ],
            )

    def test_edit_grid_to_python(self):
        # For editgrids, we need the component configuration to determine the data
        # types of its children.
        editgrid_var = SubmissionValueVariableFactory.create(
            key="editgrid",
            value=[
                {
                    "nestedEditgrid": [
                        {
                            "nested": {"date": "2000-01-01"},
                            "time": ["12:34:56", "11:22:33"],
                        },
                        {"nested": {"date": "1111-11-11"}, "time": []},
                    ]
                }
            ],
            data_type=FormVariableDataTypes.array,
            data_subtype=FormVariableDataTypes.editgrid,
            configuration={
                "type": "editgrid",
                "key": "editgrid",
                "label": "Editgrid",
                "components": [
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "components": [
                            {
                                "type": "editgrid",
                                "key": "nestedEditgrid",
                                "label": "Nested Editgrid",
                                "components": [
                                    {
                                        "type": "date",
                                        "key": "nested.date",
                                        "label": "Date",
                                    },
                                    {
                                        "type": "time",
                                        "key": "time",
                                        "label": "Time",
                                        "multiple": True,
                                    },
                                ],
                            }
                        ],
                    },
                ],
            },
        )

        editgrid_value = editgrid_var.to_python()
        self.assertEqual(
            editgrid_value,
            [
                {
                    "nestedEditgrid": [
                        {
                            "nested": {"date": date(2000, 1, 1)},
                            "time": [time(12, 34, 56), time(11, 22, 33)],
                        },
                        {"nested": {"date": date(1111, 11, 11)}, "time": []},
                    ]
                }
            ],
        )

    def test_is_initially_prefilled_is_set(self):
        config = {
            "display": "form",
            "components": [
                {
                    "key": "testPrefilled",
                    "type": "textfield",
                    "label": "Test prefilled",
                    "prefill": {
                        "plugin": "demo",
                        "attribute": "random_string",
                    },
                    "multiple": False,
                },
                {
                    "key": "testNotPrefilled",
                    "type": "textfield",
                    "label": "Test not prefilled",
                    "prefill": {
                        "plugin": "",
                        "attribute": "",
                    },
                    "multiple": False,
                },
            ],
        }

        form_step = FormStepFactory.create(form_definition__configuration=config)
        submission_step = SubmissionStepFactory.create(
            submission__form=form_step.form,
            form_step=form_step,
        )

        submission_value_variables_state = (
            submission_step.submission.load_submission_value_variables_state()
        )
        variables = submission_value_variables_state.variables

        self.assertEqual(2, len(variables))
        self.assertTrue(variables["testPrefilled"].is_initially_prefilled)
        self.assertFalse(variables["testNotPrefilled"].is_initially_prefilled)

    def test_can_store_any_json_encodable(self):
        # zeep returns objects with a __json__ method that returns a JSONValue
        class Natural:
            def __init__(self, n: int):
                if n < 1:
                    raise ValueError(f"{n} ∉ ℕ")
                self._value = n

            def __json__(self):
                return self._value

        variable1 = SubmissionValueVariableFactory.create(value=Natural(1337))
        stored = SubmissionValueVariable.objects.get(key=variable1.key)

        self.assertEqual(stored.value, 1337)

    def test_empty_value_of_date_related_components_is_serialized_before_saving(self):
        """
        Ensure that we save an empty string as an empty value for date-related
        components (we use ``None`` in our Python type domain).
        """
        for data_type in (
            FormVariableDataTypes.date,
            FormVariableDataTypes.time,
            FormVariableDataTypes.datetime,
        ):
            with self.subTest(data_type):
                variable = SubmissionValueVariableFactory.create(
                    value=None, data_type=data_type
                )

                stored = SubmissionValueVariable.objects.get(key=variable.key)
                self.assertEqual(stored.value, "")

        with self.subTest("editgrid"):
            variable = SubmissionValueVariableFactory.create(
                value=[{"date": None, "time": [None]}],
                data_type=FormVariableDataTypes.array,
                data_subtype=FormVariableDataTypes.editgrid,
                configuration={
                    "type": "editgrid",
                    "key": "editgrid",
                    "label": "Editgrid",
                    "components": [
                        {
                            "type": "date",
                            "key": "date",
                            "label": "Date",
                        },
                        {
                            "type": "time",
                            "key": "time",
                            "label": "Time",
                            "multiple": True,
                        },
                    ],
                },
            )

            stored = SubmissionValueVariable.objects.get(key=variable.key)
            self.assertEqual(stored.value, [{"date": "", "time": [""]}])


class SubmissionValueVariableManagerTests(TestCase):
    def test_create_from_data(self):
        form = FormFactory.create()
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "textfield",
                    },
                    {
                        "key": "email",
                        "type": "email",
                        "label": "email",
                    },
                ],
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form_definition__configuration={
                "components": [
                    {
                        "key": "date",
                        "type": "date",
                        "label": "date",
                    }
                ],
            },
        )

        state = submission.load_submission_value_variables_state()
        for key in ("textfield", "email", "date"):
            with self.subTest(f"Initial state: {key}"):
                variable = state.variables[key]
                # Variable is present in the state, but not in the database (yet)
                self.assertIsNone(variable.pk)
                self.assertEqual(variable.value, "")

        # Persist textfield and date to the database
        SubmissionValueVariable.objects.bulk_create_or_update_from_data(
            FormioData(
                {"textfield": "foo", "date": "2025-12-08", "non_existing": "variable"}
            ),
            submission,
        )

        # Ensure textfield and date exist
        variable = SubmissionValueVariable.objects.get(key="textfield")
        self.assertEqual(variable.value, "foo")

        variable = SubmissionValueVariable.objects.get(key="date")
        self.assertEqual(variable.value, "2025-12-08")

        # Email and non-existing variables are ignored
        self.assertFalse(SubmissionValueVariable.objects.filter(key="email").exists())
        self.assertFalse(
            SubmissionValueVariable.objects.filter(key="non_existing").exists()
        )

    def test_only_create_variables_on_step(self):
        form = FormFactory.create()
        submission = SubmissionFactory.create(form=form)
        step_1 = SubmissionStepFactory.create(
            submission=submission,
            form_step__form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "textfield",
                    }
                ],
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form_definition__configuration={
                "components": [
                    {
                        "key": "date",
                        "type": "date",
                        "label": "date",
                    }
                ],
            },
        )

        state = submission.load_submission_value_variables_state()
        for key in ("textfield", "date"):
            with self.subTest(f"Initial state: {key}"):
                variable = state.variables[key]
                # Variable is present in the state, but not in the database (yet)
                self.assertIsNone(variable.pk)
                self.assertEqual(variable.value, "")

        # Persist the textfield to the database
        SubmissionValueVariable.objects.bulk_create_or_update_from_data(
            FormioData({"textfield": "foo", "date": "2025-12-08"}), submission, step_1
        )

        # Ensure textfield exists, but date does not
        variable = SubmissionValueVariable.objects.get(key="textfield")
        self.assertEqual(variable.value, "foo")
        self.assertFalse(SubmissionValueVariable.objects.filter(key="date").exists())

    def test_update_from_data(self):
        form = FormFactory.create(
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "textfield",
                    }
                ],
            },
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionValueVariableFactory.create(
            submission=submission,
            value="foo",
            data_type=FormVariableDataTypes.string,
            key="textfield",
            configuration={
                "key": "textfield",
                "type": "textfield",
                "label": "textfield",
            },
        )

        state = submission.load_submission_value_variables_state()
        with self.subTest("Initial state"):
            variable = state.variables["textfield"]
            # Variable is present in the state, but not in the database (yet)
            self.assertIsNotNone(variable.pk)
            self.assertEqual(variable.value, "foo")

        # Update the textfield in the database
        SubmissionValueVariable.objects.bulk_create_or_update_from_data(
            FormioData({"textfield": "bar"}), submission
        )

        # Ensure textfield is updated
        variable = SubmissionValueVariable.objects.get(key="textfield")
        self.assertEqual(variable.value, "bar")

    def test_reset_variable(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "textfield",
                    },
                    {
                        "key": "date",
                        "type": "date",
                        "label": "date",
                        "defaultValue": "2000-01-01",
                    },
                ],
            },
        )
        FormVariableFactory.create(
            form=form,
            user_defined=True,
            key="user_defined",
            data_type=FormVariableDataTypes.string,
            initial_value="",
        )
        submission = SubmissionFactory.create(form=form)
        state = submission.load_submission_value_variables_state()

        # Create variables
        data = {"textfield": "foo", "date": "2025-12-05", "user_defined": "bar"}
        SubmissionValueVariable.objects.bulk_create_or_update_from_data(
            FormioData(data),
            submission,
        )
        for key, value in data.items():
            with self.subTest(f"Initial state: {key}"):
                variable = SubmissionValueVariable.objects.get(key=key)
                self.assertEqual(variable.value, value)

        # Ensure textfield is updated, and date and user_defined are deleted from the
        # database
        SubmissionValueVariable.objects.bulk_create_or_update_from_data(
            FormioData({"textfield": "bar"}),
            submission,
            reset_missing_variables=True,
        )
        variable = SubmissionValueVariable.objects.get(key="textfield")
        self.assertEqual(variable.value, "bar")
        self.assertFalse(SubmissionValueVariable.objects.filter(key="date").exists())

        # Ensure date and user_defined are still present in the state with their initial
        # value
        variable = state.variables["date"]
        self.assertIsNone(variable.pk)
        self.assertEqual(variable.value, "2000-01-01")

        variable = state.variables["user_defined"]
        self.assertIsNone(variable.pk)
        self.assertEqual(variable.value, "")
