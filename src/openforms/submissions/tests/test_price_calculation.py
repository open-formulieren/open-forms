from decimal import Decimal

from django.test import TestCase

from openforms.forms.tests.factories import FormVariableFactory
from openforms.variables.constants import FormVariableDataTypes

from ..pricing import InvalidPrice, get_submission_price
from .factories import SubmissionFactory


class PriceCalculationTests(TestCase):

    def test_price_from_related_product(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__generate_minimal_setup=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
            form__price_variable_key="",
        )
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)

        price = get_submission_price(submission=submission)

        self.assertEqual(price, Decimal("123.45"))

    def test_price_from_form_variable(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__generate_minimal_setup=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
            form__price_variable_key="",
        )
        FormVariableFactory.create(
            user_defined=True,
            key="calculatedPrice",
            form=submission.form,
            data_type=FormVariableDataTypes.float,
            # XXX this doesn't play nice with float vs. decimal, but it is what it is
            initial_value=420.69,
        )
        submission.form.price_variable_key = "calculatedPrice"
        submission.form.save()
        submission.refresh_from_db()
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)

        price = get_submission_price(submission)

        self.assertEqual(price, Decimal(420.69))

    def test_price_from_form_variable_error_cases(self):
        # Variable references can be broken in various ways, in those situation we
        # expected hard crashes.
        with self.subTest("broken variable reference"):
            submission = SubmissionFactory.create(
                completed=True,
                form__generate_minimal_setup=False,
                form__product__price=Decimal("123.45"),
                form__payment_backend="demo",
                form__price_variable_key="",
            )
            submission.form.price_variable_key = "badVariable.reference"
            submission.form.save()
            submission.refresh_from_db()

            with self.assertRaisesMessage(
                InvalidPrice,
                "No variable 'badVariable.reference' present in the submission data, "
                "refusing the temptation to guess.",
            ):
                get_submission_price(submission)

        invalid_values = (
            ("foo", FormVariableDataTypes.string),
            (["array"], FormVariableDataTypes.array),
            ({"object": "not supported"}, FormVariableDataTypes.object),
            (False, FormVariableDataTypes.boolean),
        )

        for index, (value, data_type) in enumerate(invalid_values):
            key = f"invalidValue{index}"
            with self.subTest("invalid variable values", value=value):
                submission = SubmissionFactory.create(
                    completed=True,
                    form__generate_minimal_setup=False,
                    form__product__price=Decimal("123.45"),
                    form__payment_backend="demo",
                    form__price_variable_key="",
                )
                FormVariableFactory.create(
                    user_defined=True,
                    key=key,
                    form=submission.form,
                    data_type=data_type,
                    initial_value=value,
                )
                submission.form.price_variable_key = key
                submission.form.save()
                submission.refresh_from_db()

                with self.assertRaisesMessage(
                    InvalidPrice,
                    f"Got an incompatible value type for the price variable '{key}': "
                    f"{type(value)}. We require a value that can be cast to a decimal.",
                ):
                    get_submission_price(submission)
