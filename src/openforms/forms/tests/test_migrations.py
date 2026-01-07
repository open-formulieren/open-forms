from django_test_migrations.contrib.unittest_case import MigratorTestCase

from openforms.variables.constants import FormVariableDataTypes, FormVariableSources


class StufZdsVariablesMappingMigrationTests(MigratorTestCase):
    migrate_from = (
        "forms",
        "0116_formvariable_unique_form_id_and_profile_form_variable_for_prefill_plugin_communication_preferences",
    )
    migrate_to = (
        "forms",
        "0117_stuf_zds_variables_mapping",
    )

    def prepare(self):
        apps = self.old_state.apps
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")

        form = Form.objects.create(name="Form")
        FormRegistrationBackend.objects.create(
            form=form,
            name="StUF-ZDS registration",
            key="stuf-zds-registration",
            backend="stuf-zds-create-zaak",
            options={
                "payment_status_update_mapping": [
                    {
                        "stuf_name": "payment_completed",
                        "form_variable": "payment_completed",
                    },
                    {"stuf_name": "payment_amount", "form_variable": "payment_amount"},
                    {
                        "stuf_name": "payment_public_order_ids",
                        "form_variable": "payment_public_order_ids",
                    },
                    {
                        "stuf_name": "provider_payment_ids",
                        "form_variable": "provider_payment_ids",
                    },
                ],
                "zds_zaaktype_code": "test",
                "zds_zaaktype_status_code": "",
                "zds_zaaktype_omschrijving": "",
                "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
                "zds_zaaktype_status_omschrijving": "",
                "zds_documenttype_omschrijving_inzending": "",
            },
        )

    def test_migration_with_new_variables_mapping_name(self):
        """
        Ensure that the data migration succeeds and we have the same variables in the form.
        """
        FormRegistrationBackend = self.new_state.apps.get_model(
            "forms", "FormRegistrationBackend"
        )

        backend = FormRegistrationBackend.objects.get()

        self.assertEqual(
            backend.options,
            {
                "variables_mapping": [
                    {
                        "stuf_name": "payment_completed",
                        "form_variable": "payment_completed",
                    },
                    {"stuf_name": "payment_amount", "form_variable": "payment_amount"},
                    {
                        "stuf_name": "payment_public_order_ids",
                        "form_variable": "payment_public_order_ids",
                    },
                    {
                        "stuf_name": "provider_payment_ids",
                        "form_variable": "provider_payment_ids",
                    },
                ],
                "zds_zaaktype_code": "test",
                "zds_zaaktype_status_code": "",
                "zds_zaaktype_omschrijving": "",
                "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
                "zds_zaaktype_status_omschrijving": "",
                "zds_documenttype_omschrijving_inzending": "",
            },
        )


class StufZdsReverseVariablesMappingMigrationTests(MigratorTestCase):
    migrate_from = (
        "forms",
        "0117_stuf_zds_variables_mapping",
    )
    migrate_to = (
        "forms",
        "0116_formvariable_unique_form_id_and_profile_form_variable_for_prefill_plugin_communication_preferences",
    )

    def prepare(self):
        apps = self.old_state.apps
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")

        form = Form.objects.create(name="Form")
        FormRegistrationBackend.objects.create(
            form=form,
            name="StUF-ZDS registration",
            key="stuf-zds-registration",
            backend="stuf-zds-create-zaak",
            options={
                "variables_mapping": [
                    {
                        "stuf_name": "payment_completed",
                        "form_variable": "payment_completed",
                    },
                    {"stuf_name": "payment_amount", "form_variable": "payment_amount"},
                    {
                        "stuf_name": "payment_public_order_ids",
                        "form_variable": "payment_public_order_ids",
                    },
                    {
                        "stuf_name": "provider_payment_ids",
                        "form_variable": "provider_payment_ids",
                    },
                ],
                "zds_zaaktype_code": "test",
                "zds_zaaktype_status_code": "",
                "zds_zaaktype_omschrijving": "",
                "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
                "zds_zaaktype_status_omschrijving": "",
                "zds_documenttype_omschrijving_inzending": "",
            },
        )

    def test_migration_with_new_variables_mapping_name(self):
        """
        Ensure that the data migration succeeds and we have the same variables in the form.
        """
        FormRegistrationBackend = self.new_state.apps.get_model(
            "forms", "FormRegistrationBackend"
        )

        backend = FormRegistrationBackend.objects.get()

        self.assertEqual(
            backend.options,
            {
                "payment_status_update_mapping": [
                    {
                        "stuf_name": "payment_completed",
                        "form_variable": "payment_completed",
                    },
                    {"stuf_name": "payment_amount", "form_variable": "payment_amount"},
                    {
                        "stuf_name": "payment_public_order_ids",
                        "form_variable": "payment_public_order_ids",
                    },
                    {
                        "stuf_name": "provider_payment_ids",
                        "form_variable": "provider_payment_ids",
                    },
                ],
                "zds_zaaktype_code": "test",
                "zds_zaaktype_status_code": "",
                "zds_zaaktype_omschrijving": "",
                "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
                "zds_zaaktype_status_omschrijving": "",
                "zds_documenttype_omschrijving_inzending": "",
            },
        )


class ChangeDisableLogicActionMigrationTests(MigratorTestCase):
    migrate_from = (
        "forms",
        "0118_alter_form_new_renderer_enabled",
    )
    migrate_to = (
        "forms",
        "0119_change_disable_next_logic_action",
    )

    def prepare(self):
        apps = self.old_state.apps
        Form = apps.get_model("forms", "Form")
        FormStep = apps.get_model("forms", "FormStep")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormVariable = apps.get_model("forms", "FormVariable")
        FormLogic = apps.get_model("forms", "FormLogic")

        # Form, form definitions, and form steps
        form = Form.objects.create(name="Form")
        fd_1 = FormDefinition.objects.create(
            name="fd_1",
            configuration={
                "components": [
                    {"type": "checkbox", "label": "Checkbox", "key": "checkbox"}
                ]
            },
        )
        fd_2 = FormDefinition.objects.create(
            name="fd_2",
            configuration={
                "components": [
                    {"type": "textfield", "label": "Textfield", "key": "textfield"},
                    {
                        "type": "date",
                        "label": "Date",
                        "key": "date",
                        "prefill": {
                            "plugin": "stufbg",
                            "attribute": "geboortedatum",
                            "identifierRole": "main",
                        },
                    },
                ]
            },
        )
        fd_3 = FormDefinition.objects.create(
            name="fd_3",
            configuration={
                "components": [{"type": "time", "label": "Time", "key": "time"}]
            },
        )
        FormStep.objects.create(form=form, form_definition=fd_1, order=0)
        step_2 = FormStep.objects.create(form=form, form_definition=fd_2, order=1)
        FormStep.objects.create(form=form, form_definition=fd_3, order=2)

        # Form variables
        FormVariable.objects.create(
            form=form,
            form_definition=fd_1,
            name="checkbox",
            key="checkbox",
            source=FormVariableSources.component,
            data_type=FormVariableDataTypes.boolean,
        )
        FormVariable.objects.create(
            form=form,
            form_definition=fd_2,
            name="textfield",
            key="textfield",
            source=FormVariableSources.component,
            data_type=FormVariableDataTypes.string,
        )
        FormVariable.objects.create(
            form=form,
            form_definition=fd_2,
            name="date",
            key="date",
            source=FormVariableSources.component,
            data_type=FormVariableDataTypes.string,
            prefill_plugin="stufbg",
            prefill_attribute="geboortedatum",
            prefill_identifier_role="main",
        )
        FormVariable.objects.create(
            form=form,
            form_definition=fd_3,
            name="time",
            key="time",
            source=FormVariableSources.component,
            data_type=FormVariableDataTypes.time,
        )
        FormVariable.objects.create(
            form=form,
            name="user_defined",
            key="user_defined",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.string,
        )

        # Logic rules
        FormLogic.objects.create(
            form=form,
            order=0,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
        )
        FormLogic.objects.create(
            form=form,
            order=1,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
            trigger_from_step=step_2,
        )
        FormLogic.objects.create(
            form=form,
            order=2,
            json_logic_trigger={"==": [{"var": "date"}, "2000-01-01"]},
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
        )
        FormLogic.objects.create(
            form=form,
            order=3,
            json_logic_trigger={
                "or": [
                    {"==": [{"var": "textfield"}, "foo"]},
                    {"==": [{"var": "checkbox"}, True]},
                ]
            },
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
        )
        FormLogic.objects.create(
            form=form,
            order=4,
            json_logic_trigger={
                "or": [
                    {"==": [{"var": "textfield"}, "foo"]},
                    {"==": [{"var": "checkbox"}, True]},
                    {"==": [{"var": "time"}, "12:34"]},
                ]
            },
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
            trigger_from_step=step_2,
        )
        FormLogic.objects.create(
            form=form,
            order=5,
            json_logic_trigger={"==": [{"var": "user_defined"}, "foo"]},
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
        )

    def test_migration(self):
        Form = self.new_state.apps.get_model("forms", "Form")
        form = Form.objects.get()

        steps = list(form.formstep_set.all())
        rules = list(form.formlogic_set.all())

        with self.subTest("Single input variable"):
            # Only "checkbox" from the first step is in the trigger
            self.assertEqual(len(rules[0].actions), 1)
            self.assertEqual(rules[0].actions[0]["form_step_uuid"], str(steps[0].uuid))

        with self.subTest("Trigger from step takes precedence"):
            # The "trigger_from_step" is defined on this rule, so ensure it is assigned
            # instead of the input trigger variable step (which would be the step where
            # "checkbox" is defined)
            self.assertEqual(len(rules[1].actions), 1)
            self.assertEqual(rules[1].actions[0]["form_step_uuid"], str(steps[1].uuid))

        with self.subTest("Step of input variable is ignored if field was prefilled"):
            # Components with prefill specified will have a value set upon submission
            # creation, this means executing the rule on the first step has an effect on
            # whether the user can continue. Therefore, even though the input trigger
            # contains "date" from step 2, we assign step 1 to ensure no changes in
            # behavior.
            self.assertEqual(len(rules[2].actions), 1)
            self.assertEqual(rules[2].actions[0]["form_step_uuid"], str(steps[0].uuid))

        with self.subTest("Logic trigger contains input variables from multiple steps"):
            # The logic trigger contains fields from steps 1 and 2, so ensure we add a
            # disable-next action for both
            rule = rules[3]
            self.assertEqual(len(rule.actions), 2)
            self.assertEqual(rule.actions[0]["form_step_uuid"], str(steps[0].uuid))
            self.assertEqual(rule.actions[1]["form_step_uuid"], str(steps[1].uuid))
            self.assertEqual(rule.actions[1]["action"], {"type": "disable-next"})

        with self.subTest(
            "Logic trigger contains input variables from multiple steps with "
            "trigger_form_step defined"
        ):
            # The trigger also contains "checkbox" from step 1, but it shouldn't be
            # included in the actions because the "trigger_from_step" is set to step 2.
            rule = rules[4]
            self.assertEqual(len(rule.actions), 2)
            self.assertEqual(rule.actions[0]["form_step_uuid"], str(steps[1].uuid))
            self.assertEqual(rule.actions[1]["form_step_uuid"], str(steps[2].uuid))
            self.assertEqual(rule.actions[1]["action"], {"type": "disable-next"})

        with self.subTest("With user-defined variable"):
            # The logic trigger only contains a user-defined variable, and the rule does
            # not have the "trigger_from_step" defined, so we cannot resolve a step.
            # Ensure we assign the first step as a best guess.
            self.assertEqual(len(rules[5].actions), 1)
            self.assertEqual(rules[5].actions[0]["form_step_uuid"], str(steps[0].uuid))
