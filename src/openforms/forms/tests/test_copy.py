from django.test import override_settings
from django.utils.translation import gettext as _

from rest_framework.test import APITestCase

from openforms.tests.utils import NOOP_CACHES
from openforms.variables.constants import FormVariableSources
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ..models import Form, FormDefinition, FormStep, FormVariable
from .factories import (
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)


class CopyFormTests(APITestCase):

    @override_settings(CACHES=NOOP_CACHES)
    def test_form_copy_with_reusable_definition(self):
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(is_reusable=True)
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        copied_form = form.copy()
        copied_form_step = copied_form.formstep_set.first()

        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 1)
        self.assertEqual(FormStep.objects.count(), 2)

        self.assertNotEqual(copied_form.pk, form.pk)
        self.assertNotEqual(copied_form.uuid, str(form.uuid))
        self.assertEqual(copied_form.active, form.active)
        self.assertEqual(copied_form.registration_backend, form.registration_backend)
        self.assertEqual(copied_form.name, _("{name} (copy)").format(name=form.name))
        self.assertIsNone(copied_form.product)
        self.assertEqual(copied_form.slug, _("{slug}-copy").format(slug=form.slug))

        self.assertNotEqual(copied_form_step.pk, form_step.pk)
        self.assertNotEqual(copied_form_step.uuid, str(form_step.uuid))
        self.assertEqual(copied_form_step.form.pk, copied_form.pk)
        self.assertEqual(copied_form_step.order, form_step.order)

    @override_settings(CACHES=NOOP_CACHES)
    def test_form_copy_with_non_reusable_definition(self):

        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(is_reusable=False)
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        copied_form = form.copy()
        copied_form_step = copied_form.formstep_set.first()

        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 2)
        self.assertEqual(FormStep.objects.count(), 2)

        self.assertNotEqual(copied_form_step.form_definition, form_step.form_definition)

    def test_form_copy_already_exists(self):

        form = FormFactory.create()
        copied_form_1 = form.copy()

        self.assertEqual(copied_form_1.name, _("{name} (copy)").format(name=form.name))
        self.assertEqual(copied_form_1.slug, _("{slug}-copy").format(slug=form.slug))

        copied_form_2 = form.copy()

        self.assertEqual(copied_form_2.name, _("{name} (copy)").format(name=form.name))
        self.assertEqual(copied_form_2.slug, "{}-2".format(copied_form_1.slug))

        copied_form_3 = form.copy()

        self.assertEqual(copied_form_3.name, _("{name} (copy)").format(name=form.name))
        self.assertEqual(copied_form_3.slug, "{}-3".format(copied_form_1.slug))

    def test_copy_form_with_variables(self):

        form = FormFactory.create(slug="test-copying-with-vars")
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                    },
                    {
                        "type": "textfield",
                        "key": "surname",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            source=FormVariableSources.user_defined,
            key="bla",
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(),
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"!": {"var": "bla"}},
            is_advanced=True,
            actions=[
                {
                    "action": {"type": "fetch-from-service", "value": ""},
                    "variable": "bla",
                }
            ],
        )

        self.assertEqual(1, Form.objects.count())
        self.assertEqual(3, FormVariable.objects.filter(form=form).count())
        self.assertEqual(form.formlogic_set.count(), 1)

        form_copy = form.copy()
        forms = Form.objects.all()

        self.assertEqual(2, forms.count())

        variables_copy = form_copy.formvariable_set.all()

        self.assertEqual(3, variables_copy.count())
        self.assertEqual(
            2, variables_copy.filter(source=FormVariableSources.component).count()
        )
        self.assertEqual(
            1, variables_copy.filter(source=FormVariableSources.user_defined).count()
        )
        self.assertEqual(form_copy.formlogic_set.count(), 1)

    def test_copy_form_with_registration_backends(self):
        form = FormFactory.create(slug="test-copying-with-backends")
        FormRegistrationBackendFactory.create_batch(2, form=form)

        self.assertEqual(Form.objects.count(), 1)
        self.assertEqual(form.registration_backends.count(), 2)

        form_copy = form.copy()
        forms = Form.objects.all()

        self.assertEqual(2, forms.count())

        registration_backends_copy = form_copy.registration_backends.all()

        self.assertEqual(registration_backends_copy.count(), 2)
