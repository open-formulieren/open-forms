from datetime import date, datetime, time

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from openforms.forms.tests.factories import (
    FormStepFactory,
)
from openforms.variables.constants import FormVariableDataTypes

from ...models import SubmissionValueVariable
from ..factories import SubmissionStepFactory, SubmissionValueVariableFactory


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
