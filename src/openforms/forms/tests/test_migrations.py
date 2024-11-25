from decimal import Decimal

from django.db.migrations.state import StateApps

from openforms.submissions.form_logic import check_submission_logic
from openforms.submissions.models import (
    Submission,
    SubmissionStep,
    SubmissionValueVariable,
)
from openforms.submissions.pricing import get_submission_price
from openforms.utils.tests.test_migrations import TestMigrations
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources


def _persist_user_defined_variables(submission):
    # inspired by openforms.submissions.utils.persist_user_defined_variables
    data = submission.data
    check_submission_logic(submission, data)
    state = submission.load_submission_value_variables_state()
    variables = state.variables

    user_defined_vars_data = {
        variable.key: variable.value
        for variable in variables.values()
        if variable.form_variable
        and variable.form_variable.source == FormVariableSources.user_defined
    }

    if user_defined_vars_data:
        SubmissionValueVariable.objects.bulk_create_or_update_from_data(
            user_defined_vars_data, submission
        )


class FormLogicMigrationTests(TestMigrations):
    app = "forms"
    migrate_from = "0105_alter_form_all_submissions_removal_limit_and_more"
    migrate_to = "0106_convert_price_logic_rules"

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
        form_step = FormStep.objects.create(form=form, form_definition=fd, order=1)
        amount_variable = FormVariable.objects.create(
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

        # we deliberately use the real models here to get access to the properties and
        # custom methods so that we can call get_submission_price. This requires
        # migrations to be properly orchestrated so that no schema migrations in the
        # submissions app happen at the wrong time! It could be a possible future
        # failure point.

        submission1 = Submission.objects.create(form_id=form.id)
        SubmissionStep.objects.create(submission=submission1, form_step_id=form_step.id)
        self.submission1_pk = submission1.pk
        SubmissionValueVariable.objects.create(
            submission=submission1,
            form_variable_id=amount_variable.id,
            key="amount",
            value=1.0,
        )
        price1 = get_submission_price(submission1)
        assert price1 == Decimal("4.12")

        submission2 = Submission.objects.create(form_id=form.id)
        SubmissionStep.objects.create(submission=submission2, form_step_id=form_step.id)
        self.submission2_pk = submission2.pk
        SubmissionValueVariable.objects.create(
            submission=submission2,
            form_variable_id=amount_variable.id,
            key="amount",
            value=3,
        )
        price2 = get_submission_price(submission2)
        assert price2 == Decimal("11.99")

        submission3 = Submission.objects.create(form_id=form.id)
        SubmissionStep.objects.create(submission=submission3, form_step_id=form_step.id)
        self.submission3_pk = submission3.pk
        SubmissionValueVariable.objects.create(
            submission=submission3,
            form_variable_id=amount_variable.id,
            key="amount",
            value=5,
        )
        price3 = get_submission_price(submission3)
        assert price3 == Decimal("19.99")

    def test_prices_still_the_same_after_migration(self):
        with self.subTest("submission 1"):
            submission1 = Submission.objects.get(pk=self.submission1_pk)
            _persist_user_defined_variables(submission1)

            price1 = get_submission_price(submission1)

            self.assertEqual(price1, Decimal("4.12"))

        with self.subTest("submission 2"):
            submission2 = Submission.objects.get(pk=self.submission2_pk)
            _persist_user_defined_variables(submission2)

            price2 = get_submission_price(submission2)

            self.assertEqual(price2, Decimal("11.99"))

        with self.subTest("submission 3"):
            submission3 = Submission.objects.get(pk=self.submission3_pk)
            _persist_user_defined_variables(submission3)

            price3 = get_submission_price(submission3)

            self.assertEqual(price3, Decimal("19.99"))

    def test_price_variable_created(self):
        Form = self.apps.get_model("forms", "Form")
        form = Form.objects.get()

        variables = {variable.key: variable for variable in form.formvariable_set.all()}

        self.assertIn("totalPrice", variables)
        variable = variables["totalPrice"]
        self.assertEqual(variable.data_type, FormVariableDataTypes.float)
        self.assertEqual(variable.source, FormVariableSources.user_defined)
