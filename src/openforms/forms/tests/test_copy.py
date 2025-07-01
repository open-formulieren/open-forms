from django.test import TestCase, tag
from django.utils.translation import gettext as _

from digid_eherkenning.choices import DigiDAssuranceLevels

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
    ProductFactory,
)


class CopyFormTests(TestCase):
    def test_form_copy_with_reusable_definition(self):
        form = FormFactory.create(product=None)
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
        self.assertEqual(form.registration_backends.count(), 0)
        self.assertEqual(copied_form.registration_backends.count(), 0)
        self.assertEqual(copied_form.name, _("{name} (copy)").format(name=form.name))
        self.assertIsNone(copied_form.product)
        self.assertEqual(copied_form.slug, _("{slug}-copy").format(slug=form.slug))

        self.assertNotEqual(copied_form_step.pk, form_step.pk)
        self.assertNotEqual(copied_form_step.uuid, str(form_step.uuid))
        self.assertEqual(copied_form_step.form.pk, copied_form.pk)
        self.assertEqual(copied_form_step.order, form_step.order)

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
        self.assertEqual(copied_form_2.slug, f"{copied_form_1.slug}-2")

        copied_form_3 = form.copy()

        self.assertEqual(copied_form_3.name, _("{name} (copy)").format(name=form.name))
        self.assertEqual(copied_form_3.slug, f"{copied_form_1.slug}-3")

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
        FormRegistrationBackendFactory.create_batch(2, form=form, backend="email")

        self.assertEqual(Form.objects.count(), 1)
        self.assertEqual(form.registration_backends.count(), 2)

        form_copy = form.copy()
        forms = Form.objects.all()
        # The backend_registration id and form are expected to be different,
        # compare only the values that should be the same
        backend_registrations = list(
            form.registration_backends.values("key", "name", "backend", "options")
        )
        copied_backend_registrations = list(
            form_copy.registration_backends.values("key", "name", "backend", "options")
        )

        self.assertEqual(2, forms.count())

        self.assertEqual(form_copy.registration_backends.count(), 2)
        self.assertQuerysetEqual(backend_registrations, copied_backend_registrations)

    def test_copy_form_with_logic_rules_has_correct_formstep_uuid_in_actions(self):
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(
            configuration={"components": [{"key": "test-key", "type": "textfield"}]}
        )
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "test-key"}, 1]},
            actions=[
                {
                    "action": {"type": "step-not-applicable"},
                    "form_step_uuid": str(form_step.uuid),
                }
            ],
        )

        form_copy = form.copy()
        new_form_step_uuid = form_copy.formstep_set.get().uuid
        new_form_logic_action = form_copy.formlogic_set.get().actions[0]

        self.assertEqual(
            new_form_logic_action["form_step_uuid"], str(new_form_step_uuid)
        )

    @tag("gh-4628")
    def test_copy_with_no_form_step_uuid_passed_succeeds(self):
        """
        Not all rules actions need to have a UUID specified for the form_step field
        and can accept empty strings as well (see LogicComponentActionSerializer).
        """
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(
            configuration={"components": [{"key": "test-key", "type": "textfield"}]}
        )
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "test-key"}, 1]},
            actions=[
                {"action": {"type": "disable-next"}},
                {"action": {"type": "disable-next"}, "form_step_uuid": None},
                {"action": {"type": "disable-next"}, "form_step_uuid": ""},
            ],
        )

        copied_form = form.copy()
        copied_form_step = copied_form.formstep_set.first()

        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 2)
        self.assertEqual(FormStep.objects.count(), 2)
        self.assertNotEqual(copied_form_step.form_definition, form_step.form_definition)

    def test_form_copy_with_product(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)

        copied_form = form.copy()

        self.assertEqual(copied_form.product, product)

    def test_form_copy_with_authentication_backends(self):
        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={"loa": DigiDAssuranceLevels.base},
        )

        form_authentication_backend = form.auth_backends.get()
        copied_form = form.copy()
        copied_form_authentication_backend = copied_form.auth_backends.get()

        # Assert that the configured plugin and options are the same after coping
        self.assertEqual(
            copied_form_authentication_backend.backend,
            form_authentication_backend.backend,
        )
        self.assertEqual(
            copied_form_authentication_backend.options,
            form_authentication_backend.options,
        )
