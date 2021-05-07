from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import FormDefinition
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


class FormTestCase(TestCase):
    def setUp(self) -> None:
        self.form = FormFactory.create()
        self.form_def_1 = FormDefinitionFactory.create()
        self.form_def_2 = FormDefinitionFactory.create()
        self.form_step_1 = FormStepFactory.create(
            form=self.form, form_definition=self.form_def_1
        )
        self.form_step_2 = FormStepFactory.create(
            form=self.form, form_definition=self.form_def_2
        )

    def test_login_required(self):
        self.assertFalse(self.form.login_required)
        self.form_def_2.login_required = True
        self.form_def_2.save()
        self.assertTrue(self.form.login_required)

    def test_copying_a_form(self):
        form1 = FormFactory.create(slug="a-form", name="A form")

        form2 = form1.copy()
        form3 = form1.copy()

        self.assertEqual(form2.slug, "a-form-kopie")
        self.assertEqual(form2.name, "A form (kopie)")
        self.assertEqual(form3.slug, "a-form-kopie-2")
        self.assertEqual(form3.name, "A form (kopie)")


class FormDefinitionTestCase(TestCase):
    def setUp(self) -> None:
        self.form_definition = FormDefinitionFactory.create()

    def test_deleting_form_definition_fails_when_used_by_form(self):
        self.form_definition.delete()
        self.assertFalse(
            FormDefinition.objects.filter(pk=self.form_definition.pk).exists()
        )

        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create()
        FormStepFactory.create(form=form, form_definition=form_definition)
        with self.assertRaises(ValidationError):
            form_definition.delete()
        self.assertTrue(FormDefinition.objects.filter(pk=form_definition.pk).exists())

    def test_copying_a_form_definition_makes_correct_copies(self):
        form_definition_1 = FormDefinitionFactory.create(
            slug="a-form-definition", name="A form definition"
        )

        form2 = form_definition_1.copy()
        form3 = form_definition_1.copy()

        self.assertEqual(form2.slug, "a-form-definition-kopie")
        self.assertEqual(form2.name, "A form definition (kopie)")
        self.assertEqual(form3.slug, "a-form-definition-kopie-2")
        self.assertEqual(form3.name, "A form definition (kopie)")
