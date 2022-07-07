from openforms.utils.tests.test_migrations import TestMigrations


class AddFormVariablesTests(TestMigrations):
    migrate_from = "0032_alter_formvariable_managers"
    migrate_to = "0033_formvariable_datamigration"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        FormVariable = apps.get_model("forms", "FormVariable")

        form_without_vars = Form.objects.create(
            name="Form without variables", slug="form-without-variables"
        )
        form_definition1 = FormDefinition.objects.create(
            name="Definition1",
            slug="definition1",
            configuration={
                "components": [
                    {"type": "textfield", "key": "var1"},
                    {"type": "number", "key": "var2"},
                ]
            },
        )
        FormStep.objects.create(
            form=form_without_vars, form_definition=form_definition1, order=1
        )
        form_definition2 = FormDefinition.objects.create(
            name="Definition2",
            slug="definition2",
            configuration={
                "components": [
                    {"type": "selectboxes", "key": "var3"},
                    {"type": "checkbox", "key": "var4"},
                ]
            },
        )
        FormStep.objects.create(
            form=form_without_vars,
            form_definition=form_definition2,
            order=2,
        )

        form_with_vars = Form.objects.create(
            name="Form with variables", slug="form-with-variables"
        )
        form_definition = FormDefinition.objects.create(
            name="DefinitionWithVars",
            slug="definitionWithVars",
            configuration={
                "components": [
                    {"type": "textfield", "key": "var-test"},
                ]
            },
        )
        FormStep.objects.create(
            form=form_with_vars,
            form_definition=form_definition,
            order=1,
        )
        FormVariable.objects.create(
            form=form_with_vars,
            form_definition=form_definition,
            key="var-test",
            source="component",
        )

        self.form_with_vars_id = form_with_vars.id
        self.form_without_vars_id = form_without_vars.id

    def test_add_variables(self):
        FormVariable = self.apps.get_model("forms", "FormVariable")

        new_form_component_vars = FormVariable.objects.filter(
            form__id=self.form_without_vars_id
        )
        old_form_component_vars = FormVariable.objects.filter(
            form__id=self.form_with_vars_id
        )

        self.assertEqual(1, old_form_component_vars.count())  # Was already present
        self.assertEqual(4, new_form_component_vars.count())  # Created by the migration

        var1 = new_form_component_vars.get(key="var1")
        self.assertEqual("string", var1.data_type)
        self.assertEqual("component", var1.source)
        self.assertEqual("float", new_form_component_vars.get(key="var2").data_type)
        self.assertEqual("object", new_form_component_vars.get(key="var3").data_type)
        self.assertEqual("boolean", new_form_component_vars.get(key="var4").data_type)
