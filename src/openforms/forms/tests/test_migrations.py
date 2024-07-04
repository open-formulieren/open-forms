from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources


class FixSimpleConditionalsNumbersMigrationTests(TestMigrations):
    app = "forms"
    migrate_from = "0092_v250_to_v267"
    migrate_to = "0097_v267_to_v270"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")

        bad_config = [
            {"key": "number", "type": "number", "label": "Number"},
            {"key": "currency", "type": "currency", "label": "Currency"},
            {"key": "textfield", "type": "textfield", "label": "Text Field"},
            {
                "key": "textArea1",
                "type": "textarea",
                "label": "Text Area 1",
                "conditional": {"eq": "0", "show": True, "when": "number"},
                "clearOnHide": True,
            },
            {
                "key": "textArea2",
                "type": "textarea",
                "label": "Text Area 2",
                "conditional": {"eq": "0.555", "show": True, "when": "number"},
                "clearOnHide": True,
            },
            {
                "key": "textArea3",
                "type": "textarea",
                "label": "Text Area 3",
                "conditional": {"eq": "", "show": None, "when": ""},
                "clearOnHide": True,
            },
            {
                "key": "textArea4",
                "type": "textarea",
                "label": "Text Area 4",
                "conditional": {"when": "currency", "eq": "0.55", "show": True},
                "clearOnHide": True,
            },
            {
                "key": "textArea5",
                "type": "textarea",
                "label": "Text Area 5",
                "conditional": {"eq": "1.00", "when": "currency", "show": True},
                "clearOnHide": True,
            },
            {
                "key": "textArea6",
                "type": "textarea",
                "label": "Text Area 6",
                "conditional": {"eq": "1.00", "when": "textfield", "show": True},
                "clearOnHide": True,
            },
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "label": "Repeating group",
                "components": [
                    {
                        "key": "textArea7",
                        "type": "textarea",
                        "label": "Text Area 7",
                        "conditional": {"eq": "0", "show": True, "when": "number"},
                        "clearOnHide": True,
                    },
                ],
            },
        ]
        FormDefinition.objects.create(
            name="broken", configuration={"components": bad_config}
        )

    def test_conditionals_are_fixed(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")
        fixed_components = FormDefinition.objects.get().configuration["components"]

        self.assertEqual(fixed_components[3]["conditional"]["eq"], 0)
        self.assertEqual(fixed_components[4]["conditional"]["eq"], 0.555)
        self.assertEqual(fixed_components[5]["conditional"]["eq"], "")
        self.assertEqual(fixed_components[6]["conditional"]["eq"], 0.55)
        self.assertEqual(fixed_components[7]["conditional"]["eq"], 1.0)
        self.assertEqual(fixed_components[8]["conditional"]["eq"], "1.00")
        self.assertEqual(fixed_components[9]["components"][0]["conditional"]["eq"], 0)


class FixSimpleConditionalsCheckboxesMigrationTests(TestMigrations):
    app = "forms"
    migrate_from = "0092_v250_to_v267"
    migrate_to = "0097_v267_to_v270"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")

        bad_config = [
            {"key": "checkbox", "type": "checkbox", "label": "Checkbox"},
            {"key": "textfield", "type": "textfield", "label": "Text Field"},
            {
                "key": "textArea1",
                "type": "textarea",
                "label": "Text Area 1",
                "conditional": {"eq": "true", "show": True, "when": "checkbox"},
                "clearOnHide": True,
            },
            {
                "key": "textArea2",
                "type": "textarea",
                "label": "Text Area 2",
                "conditional": {"eq": "false", "show": True, "when": "checkbox"},
                "clearOnHide": True,
            },
            {
                "key": "textArea3",
                "type": "textarea",
                "label": "Text Area 3",
                "conditional": {"eq": "", "show": None, "when": ""},
                "clearOnHide": True,
            },
            {
                "key": "textArea4",
                "type": "textarea",
                "label": "Text Area 4",
                "conditional": {"eq": "true", "when": "textfield", "show": True},
                "clearOnHide": True,
            },
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "label": "Repeating group",
                "components": [
                    {
                        "key": "textArea5",
                        "type": "textarea",
                        "label": "Text Area 5",
                        "conditional": {"eq": "true", "show": True, "when": "checkbox"},
                        "clearOnHide": True,
                    },
                ],
            },
        ]
        FormDefinition.objects.create(
            name="broken", configuration={"components": bad_config}
        )

    def test_conditionals_are_fixed(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")
        fixed_components = FormDefinition.objects.get().configuration["components"]

        self.assertTrue(isinstance(fixed_components[2]["conditional"]["eq"], bool))
        self.assertTrue(fixed_components[2]["conditional"]["eq"])
        self.assertTrue(isinstance(fixed_components[3]["conditional"]["eq"], bool))
        self.assertFalse(fixed_components[3]["conditional"]["eq"])
        self.assertEqual(fixed_components[4]["conditional"]["eq"], "")
        self.assertEqual(fixed_components[5]["conditional"]["eq"], "true")
        self.assertTrue(
            isinstance(fixed_components[6]["components"][0]["conditional"]["eq"], bool)
        )
        self.assertTrue(fixed_components[6]["components"][0]["conditional"]["eq"])


class PrefillIdentifierRoleRename(TestMigrations):
    app = "forms"
    migrate_from = "0092_v250_to_v267"
    migrate_to = "0097_v267_to_v270"

    def setUpBeforeMigration(self, apps: StateApps):
        Form = apps.get_model("forms", "Form")
        FormVariable = apps.get_model("forms", "FormVariable")
        FormDefinition = apps.get_model("forms", "FormDefinition")

        form = Form.objects.create(name="test form")

        configuration = {
            "components": [
                {
                    "type": "textfield",
                    "key": "someTextField",
                    "label": "Some textfield with prefill",
                    "prefill": {
                        "plugin": "demo",
                        "attribute": "random_string",
                        "identifierRole": "authorised_person",
                    },
                },
                {"type": "number", "key": "number", "label": "no prefill configured"},
                {
                    "type": "bsn",
                    "key": "other",
                    "label": "Some bsn field with prefill",
                    "prefill": {
                        "plugin": "demo",
                        "attribute": "random_string",
                        "identifierRole": "main",
                    },
                },
            ]
        }
        FormDefinition.objects.create(name="legacy", configuration=configuration)
        FormVariable.objects.create(
            form=form,
            form_definition=None,
            name="Prefill",
            key="prefill",
            source=FormVariableSources.user_defined,
            prefill_plugin="demo",
            prefill_attribute="random_string",
            prefill_identifier_role="authorised_person",
            data_type=FormVariableDataTypes.string,
            initial_value="",
        )

    def test_identifier_role_updated_to_authorizee(self):
        FormVariable = self.apps.get_model("forms", "FormVariable")
        FormDefinition = self.apps.get_model("forms", "FormDefinition")

        variable = FormVariable.objects.get()
        self.assertEqual(variable.prefill_identifier_role, "authorizee")

        fd = FormDefinition.objects.get()
        component = fd.configuration["components"][0]
        self.assertEqual(component["prefill"]["identifierRole"], "authorizee")
        component3 = fd.configuration["components"][2]
        self.assertEqual(component3["prefill"]["identifierRole"], "main")
