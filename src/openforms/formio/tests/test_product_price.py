import datetime
from uuid import UUID

from django.test import TestCase

from rest_framework.test import APIRequestFactory

from openforms.contrib.open_producten.tests.factories import (
    PriceFactory,
    PriceOptionFactory,
)
from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.formio.dynamic_config import rewrite_formio_components
from openforms.products.tests.factories import ProductFactory
from openforms.submissions.tests.factories import SubmissionFactory

request_factory = APIRequestFactory()


class ProductPriceConfigurationTests(TestCase):

    def setUp(self):
        self.component = {
            "type": "productPrice",
            "key": "productPrice",
            "label": "select a price option",
        }

    def test_mutate_config_dynamically_changes_type_and_adds_options(self):

        price = PriceFactory.create(valid_from=datetime.date(2024, 1, 1))
        price_option = PriceOptionFactory.create(price=price)

        config_wrapper = FormioConfigurationWrapper({"components": [self.component]})
        submission = SubmissionFactory.create(form__product=price.product_type)

        new_config_wrapper = rewrite_formio_components(config_wrapper, submission)
        new_component = new_config_wrapper.configuration["components"][0]
        self.assertEqual(
            new_component,
            {
                "type": "radio",
                "key": "productPrice",
                "label": "select a price option",
                "fieldSet": False,
                "inline": False,
                "inputType": "radio",
                "validate": {"required": True},
                "values": [
                    {
                        "label": f"{price_option.description}: € {price_option.amount}",
                        "value": UUID(price_option.uuid),
                    },
                ],
            },
        )

    def test_mutate_config_dynamically_logs_warning_when_form_has_no_product(self):

        config_wrapper = FormioConfigurationWrapper({"components": [self.component]})
        submission = SubmissionFactory.create(form__product=None)

        with self.assertLogs(
            "openforms.formio.components.custom", level="ERROR"
        ) as log:
            rewrite_formio_components(config_wrapper, submission)
            self.assertEqual(
                log.output,
                [
                    "ERROR:openforms.formio.components.custom:Form is not linked to product."
                ],
            )

    def test_mutate_config_dynamically_logs_warning_when_form_product_has_no_price(
        self,
    ):
        product = ProductFactory.create()

        config_wrapper = FormioConfigurationWrapper({"components": [self.component]})
        submission = SubmissionFactory.create(form__product=product)

        with self.assertLogs(
            "openforms.formio.components.custom", level="ERROR"
        ) as log:
            rewrite_formio_components(config_wrapper, submission)
            self.assertEqual(
                log.output,
                [
                    "ERROR:openforms.formio.components.custom:Product does not have an active price."
                ],
            )

    def test_mutate_config_dynamically_logs_warning_when_form_product_has_no_price_options(
        self,
    ):
        price = PriceFactory.create(valid_from=datetime.date(2024, 1, 1))

        config_wrapper = FormioConfigurationWrapper({"components": [self.component]})
        submission = SubmissionFactory.create(form__product=price.product_type)

        with self.assertLogs(
            "openforms.formio.components.custom", level="ERROR"
        ) as log:
            rewrite_formio_components(config_wrapper, submission)
            self.assertEqual(
                log.output,
                [
                    "ERROR:openforms.formio.components.custom:Product does not have price options."
                ],
            )
