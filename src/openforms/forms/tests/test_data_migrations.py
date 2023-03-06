from openforms.formio.utils import iter_components
from openforms.utils.tests.test_migrations import TestMigrations
from openforms.variables.constants import FormVariableDataTypes


class TestChangeOpenWhenEmptyConfiguration(TestMigrations):
    migrate_from = "0048_update_formio_default_setting"
    migrate_to = "0049_remove_editgrid_open_when_empty"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        start_components = [
            {
                "type": "editgrid",
                "key": "editgrid1",
                "components": [],
            },
            {
                "type": "editgrid",
                "key": "editgrid2",
                "openWhenEmpty": False,
                "components": [],
            },
            {
                "type": "editgrid",
                "key": "editgrid3",
                "openWhenEmpty": True,
                "components": [],
            },
            {
                "type": "fieldset",
                "key": "fieldset1",
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid4",
                        "openWhenEmpty": True,
                        "components": [],
                    },
                ],
            },
        ]
        FormDefinition.objects.create(
            name="Definition with repeating group",
            slug="definition-with-repeating-group",
            configuration={"components": start_components},
        )

    def test_open_when_empty_is_false(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")
        fd = FormDefinition.objects.get()
        components = {
            component["key"]: component
            for component in iter_components(fd.configuration)
        }

        with self.subTest("editgrid1"):
            component = components["editgrid1"]

            self.assertNotIn("openWhenEmpty", component)

        with self.subTest("editgrid2"):
            component = components["editgrid2"]

            self.assertFalse(component["openWhenEmpty"])

        with self.subTest("editgrid3"):
            component = components["editgrid3"]

            self.assertFalse(component["openWhenEmpty"])

        with self.subTest("editgrid4"):
            component = components["editgrid4"]

            self.assertFalse(component["openWhenEmpty"])


class TestFormVariableDataType(TestMigrations):
    """Assert that if type(form_component) == date, then type(form_varialbe) == date"""

    migrate_from = "0071_merge_20230213_1106"
    migrate_to = "0072_check_form_variable_datatype"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormVariable = apps.get_model("forms", "FormVariable")

        form = Form.objects.create(name="form")
        configuration = {
            "components": [
                {"key": "field1", "type": "datetime"},
                {"key": "field2", "type": "date"},
            ]
        }
        form_def = FormDefinition.objects.create(
            name="form_def",
            configuration=configuration,
        )
        FormVariable.objects.create(
            key="field1",
            form=form,
            form_definition=form_def,
            data_type=FormVariableDataTypes.datetime,
        )
        FormVariable.objects.create(
            key="field2",
            form=form,
            form_definition=form_def,
            data_type=FormVariableDataTypes.datetime,
        )
        FormVariable.objects.create(
            key="unrelated",
            form=form,
            data_type=FormVariableDataTypes.datetime,
        )

    def test_form_variable_datatype(self):
        FormVariable = self.apps.get_model("forms", "FormVariable")
        form_var1 = FormVariable.objects.filter(key="field1").first()
        form_var2 = FormVariable.objects.filter(key="field2").first()
        form_var3 = FormVariable.objects.filter(key="unrelated").first()

        # form variable 1 should be unchanged (datetime > datetime)
        self.assertEqual(form_var1.data_type, FormVariableDataTypes.datetime)

        # form variable 2 should be changed (datetime > date)
        self.assertEqual(form_var2.data_type, FormVariableDataTypes.date)

        # Sanity check: unrelated form variable should be unchanged (datetime > datetime)
        self.assertEqual(form_var3.data_type, FormVariableDataTypes.datetime)
