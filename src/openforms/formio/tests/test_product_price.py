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
from openforms.submissions.tests.factories import SubmissionFactory

request_factory = APIRequestFactory()


class ProductPriceConfigurationTests(TestCase):

    def test_mutate_config_dynamically_changes_type_and_adds_options(self):
        component = {
            "type": "productPrice",
            "key": "productPrice",
            "label": "select a price option",
        }

        price = PriceFactory.create(valid_from=datetime.date(2024, 1, 1))
        price_option = PriceOptionFactory.create(price=price)

        config_wrapper = FormioConfigurationWrapper({"components": [component]})
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

        def test_mutate_config_dynamically_changes_type_and_adds_options(self):
            component = {
                "type": "productPrice",
                "key": "productPrice",
                "label": "select a price option",
            }

            price = PriceFactory.create(valid_from=datetime.date(2024, 1, 1))
            price_option = PriceOptionFactory.create(price=price)

            config_wrapper = FormioConfigurationWrapper({"components": [component]})
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
