from datetime import date, datetime, time

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from openforms.forms.tests.factories import FormStepFactory
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

        def _assign_form_variable(submission_value_variable: SubmissionValueVariable):
            key = submission_value_variable.key
            form_var = submission_value_variable.submission.form.formvariable_set.get(
                key=key
            )
            submission_value_variable.form_variable = form_var

        with self.subTest("string"):
            string_var = SubmissionValueVariableFactory.create(
                value="a string",
                form_variable__data_type=FormVariableDataTypes.string,
                form_variable__user_defined=True,
            )
            _assign_form_variable(string_var)

            string_value = string_var.to_python()

            self.assertEqual(string_value, "a string")

        with self.subTest("boolean"):
            bool_var = SubmissionValueVariableFactory.create(
                value=True,
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.boolean,
            )
            _assign_form_variable(bool_var)

            bool_value = bool_var.to_python()

            self.assertIs(bool_value, True)

        with self.subTest("object"):
            object_var = SubmissionValueVariableFactory.create(
                value={"foo": "bar"},
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.object,
            )
            _assign_form_variable(object_var)

            object_value = object_var.to_python()

            self.assertIsInstance(object_value, dict)

        with self.subTest("array"):
            array_var = SubmissionValueVariableFactory.create(
                value=[1, 2, "foo"],
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.array,
            )
            _assign_form_variable(array_var)

            array_value = array_var.to_python()

            self.assertIsInstance(array_value, list)

        with self.subTest("int"):
            int_var = SubmissionValueVariableFactory.create(
                value=42,
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.int,
            )
            _assign_form_variable(int_var)

            int_value = int_var.to_python()

            self.assertEqual(int_value, 42)

        with self.subTest("float"):
            float_var = SubmissionValueVariableFactory.create(
                value=4.20,
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.float,
            )
            _assign_form_variable(float_var)

            float_value = float_var.to_python()

            self.assertEqual(float_value, 4.20)

        # Dates submitted by the SDK have the time part stripped off
        # User defined variables of type date also don't have the time part
        with self.subTest("date 1"):
            date_var1 = SubmissionValueVariableFactory.create(
                value="2022-09-13",
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.date,
            )
            _assign_form_variable(date_var1)

            date_value1 = date_var1.to_python()

            self.assertIsInstance(date_value1, date)
            # datetimes must be made aware in our local timezone
            self.assertEqual(
                date_value1,
                date(2022, 9, 13),
            )

        with self.subTest("date 2"):
            date_var2 = SubmissionValueVariableFactory.create(
                key="dateVar2",
                value="2022-09-13",
            )

            date_value2 = date_var2.to_python()

            # we can't infer any type info as the form-variable is disconnected
            # -> fall back to stored value
            self.assertEqual(date_value2, "2022-09-13")

        with self.subTest("datetime 1"):
            date_var3 = SubmissionValueVariableFactory.create(
                value="2022-09-13T11:10:45+02:00",
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.datetime,
            )
            _assign_form_variable(date_var3)

            date_value3 = date_var3.to_python()

            self.assertIsInstance(date_value3, datetime)
            # datetimes must be made aware in our local timezone
            self.assertIsNotNone(date_value3.tzinfo)
            expected = timezone.make_aware(datetime(2022, 9, 13, 11, 10, 45))
            self.assertEqual(date_value3, expected)

        with self.subTest("datetime 2 (naive datetime)"):
            date_var4 = SubmissionValueVariableFactory.create(
                value="2022-09-13T11:10:45",
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.datetime,
            )
            _assign_form_variable(date_var4)

            date_value4 = date_var4.to_python()

            self.assertIsInstance(date_value4, datetime)
            # datetimes must be made aware in our local timezone
            self.assertIsNotNone(date_value4.tzinfo)
            expected = timezone.make_aware(datetime(2022, 9, 13, 11, 10, 45))
            self.assertEqual(date_value4, expected)

        with self.subTest("time"):
            time_var = SubmissionValueVariableFactory.create(
                value="11:15",
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.time,
            )
            _assign_form_variable(time_var)

            time_value = time_var.to_python()

            # django does not seem to be able to make a time object tz-aware 🤔
            # we'll see if that causes any issues
            self.assertEqual(time_value, time(11, 15))

        with self.subTest("Invalid time"):
            # Issue 3647
            time_var = SubmissionValueVariableFactory.create(
                value="Invalid date",
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.time,
            )
            _assign_form_variable(time_var)

            time_value = time_var.to_python()

            self.assertIsNone(time_value)

        with self.subTest("Native time object"):
            time_var = SubmissionValueVariableFactory.create(
                value="11:15",
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.time,
            )
            _assign_form_variable(time_var)

            time_value = time_var.to_python(time(9, 41))
            self.assertEqual(time_value, time(9, 41))

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
