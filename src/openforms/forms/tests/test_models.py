from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings, tag
from django.utils.translation import gettext as _

from hypothesis import given, strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from openforms.utils.tests.feature_flags import enable_feature_flag
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..models import Form, FormDefinition, FormStep
from .factories import (
    FormAuthenticationBackendFactory,
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)


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

    def test_str(self):
        form = FormFactory.create(name="my-form")
        self.assertEqual(str(form), "my-form")

        form.internal_name = "internal"
        self.assertEqual(str(form), "internal")

        form._is_deleted = True
        self.assertEqual(
            str(form), _("{name} (deleted)").format(name=form.internal_name)
        )

    def test_registration_backend_display_single_backend(self):
        form: Form = FormFactory.create()
        FormRegistrationBackendFactory.create(form=form, key="fst", name="Backend #1")
        self.assertEqual(form.get_registration_backend_display(), "Backend #1")

    def test_registration_backend_display_multiple_backends(self):
        form: Form = FormFactory.create()
        FormRegistrationBackendFactory.create(form=form, key="fst", name="Backend #1")
        FormRegistrationBackendFactory.create(form=form, key="snd", name="Backend #2")

        self.assertEqual(
            form.get_registration_backend_display(), "Backend #1, Backend #2"
        )

    def test_form_is_unavailable_when_limit_reached(self):
        form: Form = FormFactory.create(submission_limit=2, submission_counter=2)
        self.assertFalse(form.is_available)

    def test_form_is_unavailable_when_limit_exceeded(self):
        form: Form = FormFactory.create(submission_limit=2, submission_counter=3)
        self.assertFalse(form.is_available)

    def test_form_is_available_when_limit_not_reached(self):
        form: Form = FormFactory.create(submission_limit=2, submission_counter=1)
        self.assertTrue(form.is_available)

    @override_settings(LANGUAGE_CODE="en")
    def test_registration_backend_display_marks_misconfigs(self):
        form: Form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="fst",
            name="Backend #1",
            backend="😭-admin-removed-my-plugin",
        )
        FormRegistrationBackendFactory.create(form=form, key="snd", name="Backend #2")

        self.assertEqual(
            form.get_registration_backend_display(), "Backend #1 (invalid), Backend #2"
        )

    def test_login_required(self):
        self.assertFalse(self.form.login_required)
        self.form_def_2.login_required = True
        self.form_def_2.save()
        self.assertTrue(self.form.login_required)

    def test_copying_a_form(self):
        form1 = FormFactory.create(
            slug="a-form", name="A form", internal_name="A form internal"
        )

        form2 = form1.copy()
        form3 = form1.copy()

        self.assertEqual(form2.slug, _("{slug}-copy").format(slug=form1.slug))
        self.assertEqual(form2.name, _("{name} (copy)").format(name=form1.name))
        self.assertEqual(
            form2.internal_name, _("{name} (copy)").format(name=form1.internal_name)
        )
        self.assertEqual(form3.slug, f"{form2.slug}-2")
        self.assertEqual(form3.name, _("{name} (copy)").format(name=form1.name))
        self.assertEqual(
            form3.internal_name, _("{name} (copy)").format(name=form1.internal_name)
        )

    def test_get_keys_for_email_confirmation(self):
        form = FormFactory.create()

        def_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "aaa",
                        "type": "textfield",
                        "label": "AAA",
                        "confirmationRecipient": True,
                    },
                ],
            }
        )
        def_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "bbb",
                        "type": "textfield",
                        "label": "BBB",
                        "confirmationRecipient": True,
                        "multiple": True,
                    },
                ],
            }
        )
        FormStepFactory.create(form=form, form_definition=def_1)
        FormStepFactory.create(form=form, form_definition=def_2)

        actual = form.get_keys_for_email_confirmation()
        self.assertEqual(set(actual), {"aaa", "bbb"})

    def test_iter_components(self):
        form = FormFactory.create()

        def_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "aaa",
                        "label": "AAA",
                        "type": "textfield",
                    },
                ],
            }
        )
        def_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "bbb",
                        "label": "BBB",
                        "type": "textfield",
                        "multiple": True,
                        "components": [
                            {
                                "key": "ccc",
                                "type": "textfield",
                                "label": "CCC",
                                "multiple": True,
                            },
                        ],
                    },
                ],
            }
        )
        FormStepFactory.create(form=form, form_definition=def_1)
        FormStepFactory.create(form=form, form_definition=def_2)

        with self.subTest("recursive"):
            actual = list(form.iter_components(recursive=True))
            expected = [
                {
                    "key": "aaa",
                    "label": "AAA",
                    "type": "textfield",
                },
                {
                    "key": "bbb",
                    "type": "textfield",
                    "label": "BBB",
                    "multiple": True,
                    "components": [
                        {
                            "key": "ccc",
                            "type": "textfield",
                            "label": "CCC",
                            "multiple": True,
                        },
                    ],
                },
                {
                    "key": "ccc",
                    "label": "CCC",
                    "type": "textfield",
                    "multiple": True,
                },
            ]

            self.assertEqual(actual, expected)

        with self.subTest("non-recursive"):
            actual = list(form.iter_components(recursive=False))
            expected = [
                {
                    "key": "aaa",
                    "label": "AAA",
                    "type": "textfield",
                },
                {
                    "key": "bbb",
                    "type": "textfield",
                    "label": "BBB",
                    "multiple": True,
                    "components": [
                        {
                            "key": "ccc",
                            "type": "textfield",
                            "label": "CCC",
                            "multiple": True,
                        },
                    ],
                },
            ]

            self.assertEqual(actual, expected)

    def test_iter_components_ordering(self):
        # failing test for Github #750
        form = FormFactory.create()

        def_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "bbb",
                        "label": "BBB",
                        "type": "textfield",
                    },
                ],
            }
        )
        def_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "aaa",
                        "label": "AAA",
                        "type": "textfield",
                    },
                ],
            }
        )
        # create out of order so related queryset would sort bad
        step_2 = FormStepFactory.create(form=form, form_definition=def_2)
        step_1 = FormStepFactory.create(form=form, form_definition=def_1)
        # set correct expected order
        step_2.swap(step_1)

        # check we fixed the ordering of form steps
        actual = list(form.iter_components(recursive=True))
        expected = [
            {
                "key": "aaa",
                "label": "AAA",
                "type": "textfield",
            },
            {
                "key": "bbb",
                "label": "BBB",
                "type": "textfield",
            },
        ]

        self.assertEqual(actual, expected)


class RegressionTests(HypothesisTestCase):
    @given(
        component_type=st.sampled_from(
            ["textfield", "bsn", "date", "datetime", "postcode"]
        )
    )
    @tag("gh-3922")
    def test_copy_form_with_corrupt_prefill(self, component_type):
        # bypass the factories since those enforce DB constraints
        form = FormFactory.create()
        fd = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": component_type,
                        "key": "field",
                        "label": "Field",
                        "prefill": {
                            "plugin": None,
                            "attribute": None,
                            "identifierRole": "main",
                        },
                    }
                ]
            }
        )
        FormStep.objects.create(form=form, form_definition=fd, order=0)

        form.copy()

        self.assertEqual(Form.objects.count(), 2)


class FormQuerysetTestCase(TestCase):
    def test_queryset_live(self):
        FormFactory.create(active=True, deleted_=True)
        form2 = FormFactory.create(active=True)
        FormFactory.create(active=False, deleted_=True)
        FormFactory.create(active=False)

        active = list(Form.objects.live())
        self.assertEqual(active, [form2])


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
            slug="a-form-definition",
            name="A form definition",
            internal_name="A internal",
        )

        form_definition_2 = form_definition_1.copy()
        form_definition_3 = form_definition_1.copy()

        self.assertEqual(
            form_definition_2.slug, _("{slug}-copy").format(slug="a-form-definition")
        )
        self.assertEqual(
            form_definition_2.name, _("{name} (copy)").format(name="A form definition")
        )
        self.assertEqual(
            form_definition_2.internal_name,
            _("{name} (copy)").format(name="A internal"),
        )
        self.assertEqual(form_definition_3.slug, form_definition_2.slug)
        self.assertEqual(
            form_definition_3.name, _("{name} (copy)").format(name="A form definition")
        )
        self.assertEqual(
            form_definition_3.internal_name,
            _("{name} (copy)").format(name="A internal"),
        )

    def test_get_keys_for_email_confirmation(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "aaa", "label": "AAA", "confirmationRecipient": True},
                    {"key": "bbb", "label": "BBB", "confirmationRecipient": False},
                    {"key": "ccc", "label": "CCC", "confirmationRecipient": True},
                ],
            }
        )

        keys = form_definition.get_keys_for_email_confirmation()

        self.assertIn("aaa", keys)
        self.assertNotIn("bbb", keys)
        self.assertIn("ccc", keys)

    def test_not_reusable_form_definitions_deleted(self):
        step = FormStepFactory.create(form_definition=self.form_definition)

        step.delete()

        self.assertFalse(
            FormDefinition.objects.filter(pk=step.form_definition.pk).exists()
        )

    def test_reusable_form_definition_not_deleted(self):
        reusable_form_definition = FormDefinitionFactory(is_reusable=True)
        step = FormStepFactory.create(form_definition=reusable_form_definition)

        step.delete()

        self.assertTrue(
            FormDefinition.objects.filter(pk=step.form_definition.pk).exists()
        )

    def test_form_definition_is_reusable_fails_with_multiple_forms(self):
        step = FormStepFactory.create()
        FormStepFactory.create(
            form_definition=step.form_definition,
        )
        with self.assertRaises(ValidationError):
            step.form_definition.is_reusable = False
            step.form_definition.clean()

    def test_num_components_calculated_on_save(self):
        fd = FormDefinitionFactory.build(
            configuration={
                "components": [
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "components": [
                            {
                                "type": "textfield",
                                "key": "textfield",
                            }
                        ],
                    }
                ]
            }
        )
        self.assertEqual(fd._num_components, 0)

        fd.save()

        self.assertEqual(fd._num_components, 2)

    def test_used_in_for_unsaved_fds(self):
        FormFactory.create(generate_minimal_setup=False)
        fd = FormDefinitionFactory.build()

        used_in_num = fd.used_in.count()

        self.assertEqual(used_in_num, 0)


class FormStepTestCase(TestCase):
    def test_str(self):
        step = FormStepFactory.create(
            form__internal_name="InternalForm",
            form_definition__internal_name="InternalDef",
            order=1,
        )
        expected = _("{form_name} step {order}: {definition_name}").format(
            form_name=step.form.admin_name,
            order=step.order,
            definition_name=step.form_definition.admin_name,
        )
        self.assertEqual(str(step), expected)

    def test_str_no_relation(self):
        step = FormStep()
        self.assertEqual(str(step), "FormStep object (None)")

    def test_clean(self):
        step_raises = FormStepFactory.create(
            order=0,
            is_applicable=False,
        )
        step_ok = FormStepFactory.create(
            order=0,
            is_applicable=True,
        )
        step_ok_order_1 = FormStepFactory.create(
            order=1,
            is_applicable=False,
        )
        with self.subTest("clean raises"):
            self.assertRaises(ValidationError, step_raises.clean)
        with self.subTest("clean does not raise"):
            step_ok.clean()
            step_ok_order_1.clean()


class FormLogicTests(TestCase):
    def test_block_form_logic_trigger_step_other_form(self):
        form1, form2 = FormFactory.create_batch(2)
        step = FormStepFactory.create(form=form1)
        other_step = FormStepFactory.create(form=form2)

        with self.subTest("Invalid configuration"):
            logic = FormLogicFactory.build(form=form1)
            logic.trigger_from_step = other_step
            with self.assertRaises(ValidationError):
                logic.clean()

        with self.subTest("Valid configuration"):
            logic = FormLogicFactory.build(form=form1)
            logic.trigger_from_step = step
            try:
                logic.clean()
            except ValidationError:
                self.fail("Should be allowed")

        with self.subTest("No trigger from step configured"):
            logic = FormLogicFactory.build(form=form1)
            try:
                logic.clean()
            except ValidationError:
                self.fail("Should be allowed")

    def test_input_and_output_variable_keys(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox",
                        "type": "checkbox",
                        "label": "Checkbox",
                    },
                    {
                        "key": "num.ber",
                        "type": "number",
                        "label": "Number",
                    },
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "label": "Fieldset",
                        "components": [
                            {
                                "key": "textfield",
                                "type": "textfield",
                                "label": "Textfield",
                                "clearOnHide": True,
                            },
                        ],
                    },
                ],
            },
        )
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="user_defined_number",
            form=form,
            data_type=FormVariableDataTypes.int,
        )

        rule = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {
                        "name": "Multiply user-defined variable",
                        "type": "variable",
                        "value": {"*": [{"var": "user_defined_number"}, 2]},
                    },
                    "variable": "num.ber",
                },
                {
                    "action": {
                        "name": "Non-existing variable",
                        "type": "variable",
                        "value": {"*": [{"var": "i_am_non_existing"}, 2]},
                    },
                    "variable": "num.ber",
                },
                {
                    "action": {
                        "name": "Hide fieldset",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "fieldset",
                },
            ],
        )

        self.assertEqual(rule.input_variable_keys, {"checkbox", "user_defined_number"})
        self.assertEqual(rule.output_variable_keys, {"num.ber", "textfield"})

    def test_resolve_steps(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox",
                        "type": "checkbox",
                        "label": "Checkbox",
                    },
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "label": "Fieldset",
                        "components": [
                            {
                                "key": "textfield",
                                "type": "textfield",
                                "label": "Textfield",
                                "clearOnHide": True,
                            },
                        ],
                    },
                ],
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "email",
                        "type": "email",
                        "label": "Email",
                    },
                ]
            },
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {
                        "name": "Hide fieldset",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "fieldset",
                },
            ],
        )
        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [{"var": "textfield"}, "disable email component"]
            },
            actions=[
                {
                    "action": {
                        "name": "Disable email",
                        "type": "property",
                        "property": {"value": "disabled", "type": "bool"},
                        "state": True,
                    },
                    "component": "email",
                },
            ],
        )

        with self.subTest("Rule 1"):
            self.assertEqual(rule_1.input_variable_keys, {"checkbox"})
            self.assertEqual(rule_1.output_variable_keys, {"textfield"})

            self.assertEqual(rule_1.steps, {step_1})

        with self.subTest("Rule 2"):
            self.assertEqual(rule_2.input_variable_keys, {"textfield"})
            self.assertEqual(rule_2.output_variable_keys, {"email"})

            self.assertEqual(rule_2.steps, {step_2})


class FormRegistrationBackendTests(TestCase):
    def test_string_contains_both_parts_of_the_relation(self):
        backend = FormRegistrationBackendFactory.build(
            name="Henk de Vries", form__name="zijn broer"
        )

        self.assertTrue("Henk de Vries" in str(backend))
        self.assertTrue("zijn broer" in str(backend))

    def test_backend_display_of_bad_backend(self):
        backend = FormRegistrationBackendFactory.build(backend="open-kaboose")

        self.assertEqual(backend.get_backend_display(), "-")

    def test_backend_display_of_existing_backend(self):
        backend = FormRegistrationBackendFactory.build(backend="email")

        self.assertNotEqual(backend.get_backend_display(), "-")


class FormAuthenticationBackendTests(TestCase):
    @enable_feature_flag("ENABLE_DEMO_PLUGINS")
    def test_string_contains_both_parts_of_the_relation(self):
        form = FormFactory.create(name="zijn broer")
        backend = FormAuthenticationBackendFactory.build(backend="demo", form=form)

        self.assertTrue("Demo BSN (test)" in str(backend))
        self.assertTrue("zijn broer" in str(backend))

    def test_string_of_a_non_existent_form(self):
        backend = FormAuthenticationBackendFactory.build(
            backend="demo", form__name="zijn broer"
        )

        self.assertTrue("Demo BSN (test)" in str(backend))
        self.assertTrue(_("(unsaved form)") in str(backend))

    def test_backend_display_of_bad_backend(self):
        backend = FormAuthenticationBackendFactory.build(backend="open-kaboose")

        self.assertTrue(_("unknown backend") in str(backend))
        self.assertTrue(_("(unsaved form)") in str(backend))

    @enable_feature_flag("ENABLE_DEMO_PLUGINS")
    def test_backend_display_of_existing_backend(self):
        backend = FormAuthenticationBackendFactory.build(backend="demo")

        self.assertTrue("Demo BSN (test)" in str(backend))
        self.assertTrue(_("(unsaved form)") in str(backend))
