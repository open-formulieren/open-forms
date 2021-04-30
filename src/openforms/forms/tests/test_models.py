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

    def test_deleting_form_definition(self):
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

    def test_creating_copy_of_form_definition(self):
        pre_copy_name = self.form_definition.name
        pre_copy_slug = self.form_definition.slug

        self.form_definition.copy()
        self.assertEqual(FormDefinition.objects.count(), 2)
        self.assertEqual(self.form_definition.name, f"{pre_copy_name} Kopie")
        self.assertEqual(self.form_definition.slug, f"{pre_copy_slug}-kopie")

        self.form_definition.copy()
        self.assertEqual(FormDefinition.objects.count(), 3)
        self.assertEqual(self.form_definition.name, f"{pre_copy_name} Kopie 1")
        self.assertEqual(self.form_definition.slug, f"{pre_copy_slug}-kopie1")

        self.form_definition.copy()
        self.assertEqual(FormDefinition.objects.count(), 4)
        self.assertEqual(self.form_definition.name, f"{pre_copy_name} Kopie 2")
        self.assertEqual(self.form_definition.slug, f"{pre_copy_slug}-kopie2")
