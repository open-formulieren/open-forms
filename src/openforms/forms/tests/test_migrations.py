from django_test_migrations.contrib.unittest_case import MigratorTestCase


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
