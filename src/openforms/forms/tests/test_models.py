from django.test import TestCase

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
