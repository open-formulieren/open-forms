from datetime import datetime, time

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.variables.constants import FormVariableDataTypes

from ...logic.datastructures import DataContainer
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

    def test_unique_together_submission_form_variable(self):
        variable1 = SubmissionValueVariableFactory.create()

        with self.assertRaises(IntegrityError):
            SubmissionValueVariable.objects.create(
                submission=variable1.submission, form_variable=variable1.form_variable
            )

    def test_can_create_instances(self):
        SubmissionValueVariableFactory.create()
        SubmissionValueVariableFactory.create()

    def test_get_submission_step_data(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "test1"},
                    {"type": "textfield", "key": "test2"},
                ]
            },
        )
        form_step = form.formstep_set.first()
        submission = SubmissionFactory.create(form=form)

        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"test1": "some data 1", "test2": "some data 1"},
        )

        form.formvariable_set.all().delete()

        submission_variables_state = submission.load_submission_value_variables_state()

        data_container = DataContainer(state=submission_variables_state)

        data = data_container.get_updated_step_data(submission_step)

        self.assertEqual(data, {"test1": "some data 1", "test2": "some data 1"})

    def test_to_python(self):
        """
        Test that the serialized value can be converted to native python objects.
        """
        with self.subTest("string"):
            string_var = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.string,
                value="a string",
            )

            string_value = string_var.to_python()

            self.assertEqual(string_value, "a string")

        with self.subTest("boolean"):
            bool_var = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.boolean,
                value=True,
            )

            bool_value = bool_var.to_python()

            self.assertIs(bool_value, True)

        with self.subTest("object"):
            object_var = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.object,
                value={"foo": "bar"},
            )

            object_value = object_var.to_python()

            self.assertIsInstance(object_value, dict)

        with self.subTest("array"):
            array_var = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.array,
                value=[1, 2, "foo"],
            )

            array_value = array_var.to_python()

            self.assertIsInstance(array_value, list)

        with self.subTest("int"):
            int_var = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.int,
                value=42,
            )

            int_value = int_var.to_python()

            self.assertEqual(int_value, 42)

        with self.subTest("float"):
            float_var = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.float,
                value=4.20,
            )

            float_value = float_var.to_python()

            self.assertEqual(float_value, 4.20)

        # as submitted by the SDK, the time part has been stripped off
        with self.subTest("date 1"):
            date_var1 = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.datetime,
                value="2022-09-13T00:00:00+02:00",
            )

            date_value1 = date_var1.to_python()

            self.assertIsInstance(date_value1, datetime)
            # datetimes must be made aware in our local timezone
            self.assertIsNotNone(date_value1.tzinfo)
            self.assertEqual(
                date_value1,
                timezone.make_aware(datetime(2022, 9, 13, 0, 0)),
            )

        with self.subTest("date 2"):
            date_var2 = SubmissionValueVariableFactory.create(
                form_variable=None,
                key="dateVar2",
                value="2022-09-13T00:00:00+02:00",
            )

            date_value2 = date_var2.to_python()

            # we can't infer any type info as the form-variable is disconnected
            # -> fall back to stored value
            self.assertEqual(date_value2, "2022-09-13T00:00:00+02:00")

        with self.subTest("date 3"):
            date_var3 = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.datetime,
                value="2022-09-13T11:10:45+02:00",
            )

            date_value3 = date_var3.to_python()

            self.assertIsInstance(date_value3, datetime)
            # datetimes must be made aware in our local timezone
            self.assertIsNotNone(date_value3.tzinfo)
            expected = timezone.make_aware(datetime(2022, 9, 13, 11, 10, 45))
            self.assertEqual(date_value3, expected)

        with self.subTest("date 4 (naive datetime)"):
            date_var3 = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.datetime,
                value="2022-09-13T11:10:45+02:00",
            )

            date_value3 = date_var3.to_python()

            self.assertIsInstance(date_value3, datetime)
            # datetimes must be made aware in our local timezone
            self.assertIsNotNone(date_value3.tzinfo)
            expected = timezone.make_aware(datetime(2022, 9, 13, 11, 10, 45))
            self.assertEqual(date_value3, expected)

        with self.subTest("time"):
            time_var = SubmissionValueVariableFactory.create(
                form_variable__user_defined=True,
                form_variable__data_type=FormVariableDataTypes.time,
                value="11:15",
            )

            time_value = time_var.to_python()

            # django does not seem to be able to make a time object tz-aware 🤔
            # we'll see if that causes any issues
            self.assertEqual(time_value, time(11, 15))

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
