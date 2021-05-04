import json
import os
import zipfile

from django.core.management import call_command
from django.test import TestCase

from openforms.products.tests.factories import ProductFactory

from ..models import Form, FormDefinition, FormStep
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory

PATH = os.path.abspath(os.path.dirname(__file__))


class ImportExportTests(TestCase):
    def setUp(self):
        self.filepath = os.path.join(PATH, "export_test.zip")
        self.addCleanup(lambda: os.remove(self.filepath))

    def test_export(self):
        form, _ = FormFactory.create_batch(2)
        form_definition, _ = FormDefinitionFactory.create_batch(2)
        form_step, _ = FormStepFactory.create_batch(2)
        form_step.form = form
        form_step.form_definition = form_definition
        form_step.save()

        call_command("export", form.pk, archive_name=self.filepath)

        with zipfile.ZipFile(self.filepath, "r") as f:
            self.assertEqual(
                f.namelist(), ["forms.json", "formSteps.json", "formDefinitions.json"]
            )

            forms = json.loads(f.read("forms.json"))
            self.assertEqual(len(forms), 1)
            self.assertEqual(forms[0]["uuid"], str(form.uuid))
            self.assertEqual(forms[0]["name"], form.name)
            self.assertEqual(forms[0]["slug"], form.slug)
            self.assertEqual(len(forms[0]["steps"]), form.formstep_set.count())
            self.assertIsNone(forms[0]["product"])

            form_definitions = json.loads(f.read("formDefinitions.json"))
            self.assertEqual(len(form_definitions), 1)
            self.assertEqual(form_definitions[0]["uuid"], str(form_definition.uuid))
            self.assertEqual(form_definitions[0]["name"], form_definition.name)
            self.assertEqual(form_definitions[0]["slug"], form_definition.slug)
            self.assertEqual(
                form_definitions[0]["configuration"],
                form_definition.configuration,
            )

            form_steps = json.loads(f.read("formSteps.json"))
            self.assertEqual(len(form_steps), 1)
            self.assertEqual(
                form_steps[0]["configuration"], form_definition.configuration
            )

    def test_import(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        form_pk, form_definition_pk, form_step_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
        )

        call_command("export", form.pk, archive_name=self.filepath)

        old_form_definition_slug = form_definition.slug
        form_definition.slug = "modified"
        form_definition.save()

        old_form_slug = form.slug
        form.slug = "modified"
        form.save()

        call_command("import", import_file=self.filepath)

        forms = Form.objects.all()
        self.assertEqual(forms.count(), 2)
        self.assertNotEqual(forms.last().pk, form_pk)
        self.assertNotEqual(forms.last().uuid, str(form.uuid))
        self.assertEqual(forms.last().active, False)
        self.assertEqual(forms.last().registration_backend, form.registration_backend)
        self.assertEqual(forms.last().name, form.name)
        self.assertIsNone(forms.last().product)
        self.assertEqual(forms.last().slug, old_form_slug)

        form_definitions = FormDefinition.objects.all()
        fd2 = form_definitions.last()
        self.assertEqual(form_definitions.count(), 2)
        self.assertNotEqual(fd2.pk, form_definition_pk)
        self.assertNotEqual(fd2.uuid, str(form_definition.uuid))
        self.assertEqual(fd2.configuration, form_definition.configuration)
        self.assertEqual(fd2.login_required, form_definition.login_required)
        self.assertEqual(fd2.name, form_definition.name)
        self.assertEqual(fd2.slug, old_form_definition_slug)

        form_steps = FormStep.objects.all()
        fs2 = form_steps.last()
        self.assertEqual(form_steps.count(), 2)
        self.assertNotEqual(fs2.pk, form_step_pk)
        self.assertNotEqual(fs2.uuid, str(form_step.uuid))
        self.assertEqual(fs2.availability_strategy, form_step.availability_strategy)
        self.assertEqual(fs2.form.pk, forms.last().pk)
        self.assertEqual(fs2.form_definition.pk, fd2.pk)
        self.assertEqual(fs2.optional, form_step.optional)
        self.assertEqual(fs2.order, form_step.order)
