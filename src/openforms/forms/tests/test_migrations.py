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
