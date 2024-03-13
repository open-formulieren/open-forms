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
