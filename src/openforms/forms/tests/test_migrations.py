from decimal import Decimal

from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources


class FormLogicMigrationTests(TestMigrations):
    app = "forms"
    migrate_from = "0097_v267_to_v270"
    migrate_to = "0098_v270_to_v300"

    def setUpBeforeMigration(self, apps: StateApps):
        # set up some variants that will each be hit for different submissions. After
        # migrating to form variable pricing, the result must be the same.
        Product = apps.get_model("products", "Product")
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        FormPriceLogic = apps.get_model("forms", "FormPriceLogic")
        FormVariable = apps.get_model("forms", "FormVariable")

        product = Product.objects.create(name="Test product", price=Decimal("4.12"))
        fd = FormDefinition.objects.create(
            name="Pricing tests", configuration={"components": []}
        )
        form = Form.objects.create(name="Pricing tests", product=product, slug="step-1")
        FormStep.objects.create(form=form, form_definition=fd, order=1)
        FormVariable.objects.create(
            form=form,
            name="Amount",
            key="amount",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.float,
            initial_value=1.0,
        )
        FormPriceLogic.objects.create(
            form=form,
            json_logic_trigger={"==": [{"var": "amount"}, 3]},
            price=Decimal("11.99"),
        )
        FormPriceLogic.objects.create(
            form=form,
            json_logic_trigger={"==": [{"var": "amount"}, 5]},
            price=Decimal("19.99"),
        )

    def test_price_variable_created(self):
        Form = self.apps.get_model("forms", "Form")
        form = Form.objects.get()

        variables = {variable.key: variable for variable in form.formvariable_set.all()}

        self.assertIn("totalPrice", variables)
        variable = variables["totalPrice"]
        self.assertEqual(variable.data_type, FormVariableDataTypes.float)
        self.assertEqual(variable.source, FormVariableSources.user_defined)


class DuplicatePriceVariableMigrationTests(TestMigrations):
    app = "forms"
    migrate_from = "0097_v267_to_v270"
    migrate_to = "0098_v270_to_v300"

    def setUpBeforeMigration(self, apps: StateApps):
        # set up some variants that will each be hit for different submissions. After
        # migrating to form variable pricing, the result must be the same.
        Product = apps.get_model("products", "Product")
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        FormPriceLogic = apps.get_model("forms", "FormPriceLogic")
        FormVariable = apps.get_model("forms", "FormVariable")

        product = Product.objects.create(name="Test product", price=Decimal("4.12"))
        fd = FormDefinition.objects.create(
            name="Pricing tests", configuration={"components": []}
        )
        form = Form.objects.create(name="Pricing tests", product=product, slug="step-1")
        FormStep.objects.create(form=form, form_definition=fd, order=1)
        FormPriceLogic.objects.create(
            form=form,
            json_logic_trigger={"==": [{"var": "amount"}, 3]},
            price=Decimal("11.99"),
        )
        FormVariable.objects.create(
            form=form,
            name="Amount",
            key="amount",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.float,
            initial_value=1.0,
        )
        # causes conflicts
        FormVariable.objects.create(
            form=form,
            name="Total price",
            key="totalPrice",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.float,
            initial_value=10.0,
        )

    def test_price_variable_created(self):
        Form = self.apps.get_model("forms", "Form")
        form = Form.objects.get()

        variables = {variable.key: variable for variable in form.formvariable_set.all()}

        self.assertIn("totalPrice", variables)  # pre-existing
        self.assertIn("totalPrice1", variables)  # newly created
        variable = variables["totalPrice1"]
        self.assertEqual(variable.data_type, FormVariableDataTypes.float)
        self.assertEqual(variable.source, FormVariableSources.user_defined)
        self.assertEqual(form.price_variable_key, "totalPrice1")
