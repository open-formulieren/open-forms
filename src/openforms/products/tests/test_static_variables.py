from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.variables.service import get_static_variables


class TestProductStaticVariables(SubmissionsMixin, TestCase):
    def test_product_static_data(self):
        submission = SubmissionFactory.create(
            form__product__name="test_prod",
            form__product__price=9.99,
            form__product__information="Let Op!",
        )

        static_data = {
            variable.key: variable
            for variable in get_static_variables(submission=submission)
        }

        self.assertIn("product", static_data)
        self.assertEqual(static_data["product"].initial_value["name"], "test_prod")
        self.assertEqual(static_data["product"].initial_value["price"], 9.99)
        self.assertEqual(static_data["product"].initial_value["information"], "Let Op!")

    def test_product_static_data_no_submission(self):
        static_data = {variable.key: variable for variable in get_static_variables()}

        self.assertIn("product", static_data)
        self.assertIsNone(static_data["product"].initial_value)
