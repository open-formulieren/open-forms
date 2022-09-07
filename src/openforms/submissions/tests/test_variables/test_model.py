from django.db import IntegrityError
from django.test import TestCase

from openforms.forms.tests.factories import FormFactory

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
