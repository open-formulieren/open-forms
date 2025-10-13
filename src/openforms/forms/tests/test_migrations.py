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
