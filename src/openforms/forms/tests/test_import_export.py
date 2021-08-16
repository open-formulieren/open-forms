import json
import os
import zipfile

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from openforms.products.tests.factories import ProductFactory

from ...submissions.tests.form_logic.factories import FormLogicFactory
from ..models import Form, FormDefinition, FormLogic, FormStep
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory

PATH = os.path.abspath(os.path.dirname(__file__))


class ImportExportTests(TestCase):
    def setUp(self):
        self.filepath = os.path.join(PATH, "export_test.zip")

        def remove_file():
            try:
                os.remove(self.filepath)
            except Exception:
                pass

        self.addCleanup(remove_file)

    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_export(self):
        form, _ = FormFactory.create_batch(2, authentication_backends=["demo"])
        form_definition, _ = FormDefinitionFactory.create_batch(2)
        form_step, _ = FormStepFactory.create_batch(2)
        form_step.form = form
        form_step.form_definition = form_definition
        form_step.save()
        FormLogicFactory.create(
            form=form,
            actions=[
                {
                    "component": "test_component",
                    "action": "test action",
                }
            ],
        )

        call_command("export", form.pk, self.filepath)

        with zipfile.ZipFile(self.filepath, "r") as f:
            self.assertEqual(
                f.namelist(),
                [
                    "forms.json",
                    "formSteps.json",
                    "formDefinitions.json",
                    "formLogic.json",
                ],
            )

            forms = json.loads(f.read("forms.json"))
            self.assertEqual(len(forms), 1)
            self.assertEqual(forms[0]["uuid"], str(form.uuid))
            self.assertEqual(forms[0]["name"], form.name)
            self.assertEqual(forms[0]["slug"], form.slug)
            self.assertEqual(forms[0]["authentication_backends"], ["demo"])
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

            form_logic = json.loads(f.read("formLogic.json"))
            self.assertEqual(1, len(form_logic))
            self.assertEqual("test_component", form_logic[0]["actions"][0]["component"])
            self.assertEqual("test action", form_logic[0]["actions"][0]["action"])
            self.assertIn(str(form.uuid), form_logic[0]["form"])

    def test_import(self):
        product = ProductFactory.create()
        form = FormFactory.create(
            product=product, authentication_backends=["demo"], payment_backend="demo"
        )
        form_definition = FormDefinitionFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_logic = FormLogicFactory.create(form=form)

        form_pk, form_definition_pk, form_step_pk, form_logic_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
            form_logic.pk,
        )

        call_command("export", form.pk, self.filepath)

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
        self.assertEqual(forms.last().authentication_backends, ["demo"])
        self.assertEqual(forms.last().payment_backend, "demo")

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

        form_logics = FormLogic.objects.all()
        self.assertEqual(2, form_logics.count())
        form_logic_2 = form_logics.last()
        self.assertNotEqual(form_logic_2.pk, form_logic_pk)
        self.assertNotEqual(form_logic_2.uuid, str(form_logic.uuid))
        self.assertEqual(form_logic_2.form.pk, forms.last().pk)

    def test_import_no_backends(self):
        """
        explicitly test import/export of Form without backends as they use custom fields/choices
        """
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        call_command("export", form.pk, self.filepath)

        form_definition.slug = "modified"
        form_definition.save()
        form.slug = "modified"
        form.save()

        call_command("import", import_file=self.filepath)

    def test_import_form_slug_already_exists(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_logic = FormLogicFactory.create(form=form)

        form_pk, form_definition_pk, form_step_pk, form_logic_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
            form_logic.pk,
        )

        call_command("export", form.pk, self.filepath)

        old_form_definition_slug = form_definition.slug
        form_definition.slug = "modified"
        form_definition.save()

        with self.assertRaises(CommandError):
            call_command("import", import_file=self.filepath)

        forms = Form.objects.all()
        self.assertEqual(forms.count(), 1)
        self.assertEqual(forms.last().pk, form_pk)
        self.assertEqual(forms.last().uuid, str(form.uuid))
        self.assertEqual(forms.last().active, form.active)
        self.assertEqual(forms.last().registration_backend, form.registration_backend)
        self.assertEqual(forms.last().name, form.name)
        self.assertEqual(forms.last().product, form.product)
        self.assertEqual(forms.last().slug, form.slug)

        form_definitions = FormDefinition.objects.all()
        fd2 = form_definitions.last()
        self.assertEqual(form_definitions.count(), 1)
        self.assertEqual(fd2.pk, form_definition_pk)
        self.assertEqual(fd2.uuid, str(form_definition.uuid))
        self.assertEqual(fd2.configuration, form_definition.configuration)
        self.assertEqual(fd2.login_required, form_definition.login_required)
        self.assertEqual(fd2.name, form_definition.name)
        self.assertEqual(fd2.slug, form_definition.slug)

        form_steps = FormStep.objects.all()
        fs2 = form_steps.last()
        self.assertEqual(form_steps.count(), 1)
        self.assertEqual(fs2.pk, form_step_pk)
        self.assertEqual(fs2.uuid, str(form_step.uuid))
        self.assertEqual(fs2.availability_strategy, form_step.availability_strategy)
        self.assertEqual(fs2.form.pk, forms.last().pk)
        self.assertEqual(fs2.form_definition.pk, fd2.pk)
        self.assertEqual(fs2.optional, form_step.optional)
        self.assertEqual(fs2.order, form_step.order)

        form_logics = FormLogic.objects.all()
        form_logic_2 = form_logics.last()
        self.assertEqual(form_logics.count(), 1)
        self.assertEqual(form_logic_2.pk, form_logic_pk)
        self.assertEqual(forms.last().pk, form_logic_2.form.pk)

    def test_import_form_definition_slug_already_exists_configuration_duplicate(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_logic = FormLogicFactory.create(form=form)

        form_pk, form_definition_pk, form_step_pk, form_logic_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
            form_logic.pk,
        )

        call_command("export", form.pk, self.filepath)

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
        self.assertEqual(form_definitions.count(), 1)
        self.assertEqual(fd2.pk, form_definition_pk)
        self.assertEqual(fd2.uuid, str(form_definition.uuid))
        self.assertEqual(fd2.configuration, form_definition.configuration)
        self.assertEqual(fd2.login_required, form_definition.login_required)
        self.assertEqual(fd2.name, form_definition.name)
        self.assertEqual(fd2.slug, form_definition.slug)

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

        form_logics = FormLogic.objects.all()
        form_logic_2 = form_logics.last()
        self.assertEqual(form_logics.count(), 2)
        self.assertNotEqual(form_logic_2.pk, form_logic_pk)
        self.assertEqual(forms.last().pk, form_logic_2.form.pk)

    def test_import_form_definition_slug_already_exists_configuration_different(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_logic = FormLogicFactory.create(form=form)

        form_pk, form_definition_pk, form_step_pk, form_logic_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
            form_logic.pk,
        )

        call_command("export", form.pk, self.filepath)

        old_form_slug = form.slug
        form.slug = "modified"
        form.save()

        old_fd_config = form_definition.configuration
        form_definition.configuration = {"foo": ["bar"]}
        form_definition.save()

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
        self.assertEqual(fd2.configuration, old_fd_config)
        self.assertEqual(fd2.login_required, form_definition.login_required)
        self.assertEqual(fd2.name, form_definition.name)
        self.assertEqual(fd2.slug, f"{form_definition.slug}-2")

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

        form_logics = FormLogic.objects.all()
        form_logic_2 = form_logics.last()
        self.assertEqual(form_logics.count(), 2)
        self.assertNotEqual(form_logic_2.pk, form_logic_pk)
        self.assertEqual(forms.last().pk, form_logic_2.form.pk)
