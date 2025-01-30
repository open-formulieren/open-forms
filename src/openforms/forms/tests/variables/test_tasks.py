from django.test import TestCase, override_settings

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ...models import FormVariable
from ...tasks import on_variables_bulk_update_event


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OnVariablesBulkUpdateEventTests(TestCase):
    def test_on_variables_bulk_update_event(self):
        form = FormFactory.create()
        other_form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "firstName",
                        "type": "textfield",
                        "label": "First Name",
                    },
                    {
                        "key": "lastName",
                        "type": "textfield",
                        "label": "Last Name",
                    },
                ],
            },
            is_reusable=True,
        )
        form_step1 = FormStepFactory.create(form=form, form_definition=form_definition)
        form_step2 = FormStepFactory.create(
            form=other_form, form_definition=form_definition
        )

        submission1 = SubmissionFactory.create(form=form)
        submission2 = SubmissionFactory.create(form=other_form)

        SubmissionStepFactory.create(
            submission=submission1,
            form_step=form_step1,
            data={"firstName": "John"},
        )
        SubmissionStepFactory.create(
            submission=submission2,
            form_step=form_step2,
            data={"firstName": "John"},
        )

        on_variables_bulk_update_event(form.id)

        with self.subTest("Form has appropriate FormVariables"):
            self.assertEqual(FormVariable.objects.filter(form=form).count(), 2)
            first_name_var1, last_name_var1 = FormVariable.objects.filter(
                form=form
            ).order_by("pk")
            self.assertEqual(first_name_var1.key, "firstName")
            self.assertEqual(last_name_var1.key, "lastName")

        with self.subTest(
            "other Form that reuses this FormDefinition has appropriate FormVariables"
        ):
            self.assertEqual(FormVariable.objects.filter(form=other_form).count(), 2)

            first_name_var2, last_name_var2 = FormVariable.objects.filter(
                form=other_form
            ).order_by("pk")

            self.assertEqual(first_name_var2.key, "firstName")
            self.assertEqual(last_name_var2.key, "lastName")
