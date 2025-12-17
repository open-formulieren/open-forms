from openforms.utils.tests.test_migrations import TestMigrations


class DataTypeMigrationTests(TestMigrations):
    migrate_from = "0109_formvariable_data_type_and_data_subtype"
    migrate_to = "0111_formvariable_form_variable_subtype_empty_iff_data_type_is_not_array_and_more"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormVariable = apps.get_model("forms", "FormVariable")
        FormDefinition = apps.get_model("forms", "FormDefinition")

        form = Form.objects.create(name="Form")
        fd = FormDefinition.objects.create(
            name="Form definition",
            configuration={
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "Textfield"}
                ]
            },
        )
        # Form variable for which the key is not present in the configuration
        FormVariable.objects.create(
            form=form,
            form_definition=fd,
            name="Non-existing key",
            key="nonExistingKey",
            source="component",
            data_type="array",
            data_subtype="",
        )

    def test_migration_with_outdated_form_variable(self):
        """
        Ensure that the migration succeeds when a form variable has a key that is not
        present in the corresponding form definition configuration.

        Note that this situation shouldn't occur, but *could* when someone manually
        changes a form variable and/or form definition configuration.
        """
        FormVariable = self.apps.get_model("forms", "FormVariable")

        variable = FormVariable.objects.get(key="nonExistingKey")
        self.assertEqual(variable.data_subtype, "string")


class StufZdsVariablesMappingMigrationTests(TestMigrations):
    migrate_from = "0116_formvariable_unique_form_id_and_profile_form_variable_for_prefill_plugin_communication_preferences"
    migrate_to = "0117_stuf_zds_variables_mapping"
    app = "forms"

    def setUpBeforeMigration(self, apps):
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
        FormRegistrationBackend = self.apps.get_model(
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


class StufZdsReverseVariablesMappingMigrationTests(TestMigrations):
    migrate_from = "0117_stuf_zds_variables_mapping"
    migrate_to = "0116_formvariable_unique_form_id_and_profile_form_variable_for_prefill_plugin_communication_preferences"
    app = "forms"

    def setUpBeforeMigration(self, apps):
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
        FormRegistrationBackend = self.apps.get_model(
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
