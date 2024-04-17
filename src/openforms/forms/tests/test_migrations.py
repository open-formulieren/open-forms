from zgw_consumers.constants import APITypes, AuthTypes

from openforms.utils.tests.test_migrations import TestMigrations
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources


class EnableNewBuilderMigrationTests(TestMigrations):
    app = "forms"
    migrate_from = "0093_fix_prefill_bis"
    migrate_to = "0094_convert_old_service_fetch_config"

    def setUpBeforeMigration(self, apps):
        FormVariable = apps.get_model("forms", "FormVariable")
        Form = apps.get_model("forms", "Form")
        FormLogic = apps.get_model("forms", "FormLogic")
        Service = apps.get_model("zgw_consumers", "Service")
        ServiceFetchConfiguration = apps.get_model(
            "variables", "ServiceFetchConfiguration"
        )

        service = Service.objects.create(
            label="Test",
            api_type=APITypes.orc,
            auth_type=AuthTypes.no_auth,
        )
        config = ServiceFetchConfiguration.objects.create(
            service=service,
            name="Test Service",
        )

        form = Form.objects.create(name="test form")
        FormVariable.objects.create(
            form=form,
            name="Var 1",
            key="var1",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.string,
        )
        FormVariable.objects.create(
            form=form,
            name="Var 2",
            key="var2",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.string,
        )
        FormLogic.objects.create(
            order=0,
            form=form,
            json_logic_trigger={"!!": [True]},
            actions=[
                {
                    "action": {
                        "type": "fetch-from-service",
                        "value": str(config.pk),  # An existing service
                    },
                    "variable": "var1",
                    "component": "",
                    "form_step": "",
                    "form_step_uuid": None,
                }
            ],
        )
        FormLogic.objects.create(
            order=1,
            form=form,
            json_logic_trigger={"!!": [True]},
            actions=[
                {
                    "action": {
                        "type": "fetch-from-service",
                        "value": "4000",  # A non-existing service
                    },
                    "variable": "var2",
                    "component": "",
                    "form_step": "",
                    "form_step_uuid": None,
                }
            ],
        )
        FormLogic.objects.create(
            order=0,
            form=form,
            json_logic_trigger={"!!": [True]},
            actions=[
                {
                    "action": {
                        "type": "fetch-from-service",
                        "value": config.pk,  # An existing service, but with an int value instead of string
                    },
                    "variable": "var1",
                    "component": "",
                    "form_step": "",
                    "form_step_uuid": None,
                }
            ],
        )
        self.form = form

    def test_builder_enabled(self):
        rules = self.form.formlogic_set.all().order_by("order")

        self.assertEqual(rules[0].actions[0]["action"]["value"], "")
        self.assertEqual(rules[1].actions[0]["action"]["value"], "")
        self.assertEqual(rules[2].actions[0]["action"]["value"], "")

        variables = self.form.formvariable_set.all().order_by("key")

        self.assertIsNotNone(variables[0].service_fetch_configuration)
        self.assertIsNone(variables[1].service_fetch_configuration)


class FixValidateConfigurationMigrationTests(TestMigrations):
    app = "forms"
    migrate_from = "0095_merge_20240313_1742"
    migrate_to = "0096_fix_invalid_validate_configuration"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")

        bad_config = [
            {
                "type": "textfield",
                "key": "textfield",
                "key": "textfield",
                "validate": {
                    "minLength": "",
                    "maxLength": "",
                },
            },
            {
                "type": "email",
                "key": "email",
                "key": "email",
                "validate": {
                    "minLength": "",
                    "maxLength": "",
                },
            },
            {
                "type": "phoneNumber",
                "key": "phoneNumber",
                "key": "phoneNumber",
                "validate": {
                    "minLength": "",
                    "maxLength": "",
                },
            },
            {
                "type": "postcode",
                "key": "postcode",
                "key": "postcode",
                "validate": {
                    "minLength": "",
                    "maxLength": "",
                },
            },
            {
                "type": "textarea",
                "key": "textarea",
                "key": "textarea",
                "validate": {
                    "minLength": "",
                    "maxLength": "",
                    "minWords": "",
                    "maxWords": "",
                },
            },
            {
                "type": "number",
                "key": "number",
                "key": "number",
                "validate": {
                    "min": "",
                    "max": "",
                },
            },
            {
                "type": "currency",
                "key": "currency",
                "key": "currency",
                "validate": {
                    "min": "",
                    "max": "",
                },
            },
            {
                "type": "iban",
                "key": "iban",
                "key": "iban",
                "validate": {
                    "minLength": "",
                    "maxLength": "",
                },
            },
            {
                "type": "licenseplate",
                "key": "licenseplate",
                "key": "licenseplate",
                "validate": {
                    "minLength": "",
                    "maxLength": "",
                },
            },
            {
                "type": "bsn",
                "key": "bsn",
                "key": "bsn",
                "validate": {
                    "minLength": "",
                    "maxLength": "",
                },
            },
            {
                "type": "cosign",
                "key": "cosign",
                "key": "cosign",
                "validate": {
                    "minLength": "",
                    "maxLength": "",
                },
            },
        ]
        FormDefinition.objects.create(
            name="broken", configuration={"components": bad_config}
        )

    def test_migration_fixes_issues(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")
        fixed_config = FormDefinition.objects.get().configuration["components"]

        (
            textfield,
            email,
            phone_number,
            postcode,
            textarea,
            number,
            currency,
            iban,
            licenseplate,
            bsn,
            cosign,
        ) = fixed_config

        with self.subTest("textfield"):
            self.assertNotIn("minLength", textfield["validate"])
            self.assertNotIn("maxLength", textfield["validate"])

        with self.subTest("email"):
            self.assertNotIn("minLength", email["validate"])
            self.assertNotIn("maxLength", email["validate"])

        with self.subTest("phone_number"):
            self.assertNotIn("minLength", phone_number["validate"])
            self.assertNotIn("maxLength", phone_number["validate"])

        with self.subTest("postcode"):
            self.assertNotIn("minLength", postcode["validate"])
            self.assertNotIn("maxLength", postcode["validate"])

        with self.subTest("textarea"):
            self.assertNotIn("minLength", textarea["validate"])
            self.assertNotIn("maxLength", textarea["validate"])
            self.assertNotIn("minWords", textarea["validate"])
            self.assertNotIn("maxWords", textarea["validate"])

        with self.subTest("number"):
            self.assertNotIn("min", number["validate"])
            self.assertNotIn("max", number["validate"])

        with self.subTest("currency"):
            self.assertNotIn("min", currency["validate"])
            self.assertNotIn("max", currency["validate"])

        with self.subTest("iban"):
            self.assertNotIn("minLength", iban["validate"])
            self.assertNotIn("maxLength", iban["validate"])

        with self.subTest("licenseplate"):
            self.assertNotIn("minLength", licenseplate["validate"])
            self.assertNotIn("maxLength", licenseplate["validate"])

        with self.subTest("bsn"):
            self.assertNotIn("minLength", bsn["validate"])
            self.assertNotIn("maxLength", bsn["validate"])

        with self.subTest("cosign"):
            self.assertNotIn("minLength", cosign["validate"])
            self.assertNotIn("maxLength", cosign["validate"])


class FixSimpleConditionalsNumbersMigrationTests(TestMigrations):
    app = "forms"
    migrate_from = "0096_fix_invalid_validate_configuration"
    migrate_to = "0097_fix_forms_conditionals"

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

        self.assertTrue(isinstance(fixed_components[3]["conditional"]["eq"], int))
        self.assertTrue(isinstance(fixed_components[4]["conditional"]["eq"], float))
        self.assertTrue(isinstance(fixed_components[5]["conditional"]["eq"], str))
        self.assertTrue(isinstance(fixed_components[6]["conditional"]["eq"], float))
        self.assertTrue(isinstance(fixed_components[7]["conditional"]["eq"], float))
        self.assertTrue(isinstance(fixed_components[8]["conditional"]["eq"], str))
        self.assertTrue(
            isinstance(fixed_components[9]["components"][0]["conditional"]["eq"], int)
        )


class FixSimpleConditionalsCheckboxesMigrationTests(TestMigrations):
    app = "forms"
    migrate_from = "0096_fix_invalid_validate_configuration"
    migrate_to = "0097_fix_forms_conditionals"

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
