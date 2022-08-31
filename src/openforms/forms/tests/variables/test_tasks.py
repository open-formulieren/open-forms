from django.test import TestCase

from openforms.forms.tasks import recouple_submission_variables_to_form_variables
from openforms.forms.tests.factories import FormFactory, FormVariableFactory
from openforms.submissions.models import SubmissionValueVariable
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)


class FormVariableTasksTest(TestCase):
    def test_recouple_submission_variables(self):
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
        submission1 = SubmissionFactory.create(form=form)
        submission2 = SubmissionFactory.create(form=form)

        SubmissionStepFactory.create(
            submission=submission1,
            form_step=form_step,
            data={"test1": "some data 1", "test2": "some data 1"},
        )
        SubmissionStepFactory.create(
            submission=submission2,
            form_step=form_step,
            data={"test1": "some other data 1", "test2": "some other data 1"},
        )

        form.formvariable_set.all().delete()

        self.assertEqual(
            4,
            SubmissionValueVariable.objects.filter(
                submission__form=form, form_variable__isnull=True
            ).count(),
        )

        FormVariableFactory.create(key="test1", form=form)
        FormVariableFactory.create(key="test2", form=form)

        recouple_submission_variables_to_form_variables(form.id)

        self.assertEqual(
            0,
            SubmissionValueVariable.objects.filter(
                submission__form=form, form_variable__isnull=True
            ).count(),
        )
