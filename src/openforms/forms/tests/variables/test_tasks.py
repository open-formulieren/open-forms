from django.test import TestCase, override_settings, tag

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
from ...tasks import (
    create_form_variables_for_components,
    on_formstep_save_event,
    on_variables_bulk_update_event,
)


@tag("gh-4824")
class CreateFormVariablesForComponentsTests(TestCase):
    def test_create_form_variables_for_components(self):
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "lastName",
                        "type": "textfield",
                        "label": "Last Name",
                    },
                ],
            }
        )
        FormStepFactory.create(form=form, form_definition=form_definition)

        # Form is in a broken state, because no FormVariable exists for `lastName`
        FormVariable.objects.filter(form=form).delete()

        with self.subTest("create variables for components"):
            create_form_variables_for_components(form.id)

            variables = FormVariable.objects.filter(form=form)

            self.assertEqual(variables.count(), 1)

            [variable] = variables

            self.assertEqual(variable.form_definition, form_definition)
            self.assertEqual(variable.source, "component")
            self.assertEqual(variable.key, "lastName")

        with self.subTest("task is idempotent"):
            create_form_variables_for_components(form.id)

            variables = FormVariable.objects.filter(form=form)

            self.assertEqual(variables.count(), 1)


@tag("gh-4824")
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OnFormStepSaveEventTests(TestCase):
    def test_on_formstep_save_event_fixes_broken_form_variables_state(self):
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

        # Form is in a broken state, because no FormVariable exists for `lastName`
        # Simulating the scenario where `lastName` was added but no variable was created
        # because there are errors in the variables tab
        FormVariable.objects.filter(form=form, key="lastName").delete()
        FormVariable.objects.filter(form=other_form, key="lastName").delete()

        on_formstep_save_event(form.id, 60)

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
