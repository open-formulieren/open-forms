from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from ...contrib.open_producten.tests.factories import PriceFactory
from ...products.tests.factories import ProductFactory
from ..validators import validate_formio_js_schema, validate_price_option
from .factories import FormDefinitionFactory


class FormioJSSchemaValidatorTests(SimpleTestCase):
    def test_valid_schemas(self):
        valid = [
            {"components": []},
            {
                "components": [
                    {
                        "type": "foo",
                        "components": [],
                    }
                ]
            },
        ]

        for schema in valid:
            with self.subTest(schema=schema):
                try:
                    validate_formio_js_schema(schema)
                except ValidationError as exc:
                    self.fail(f"Unexpected validation error: {exc}")

    def test_invalid_schemas(self):
        invalid = [
            {},
            [],
            None,
            {"anything": "else"},
            {"components": None},
            {"components": {}},
        ]

        for schema in invalid:
            with self.subTest(schema=schema):
                with self.assertRaises(ValidationError):
                    validate_formio_js_schema(schema)


class OpenProductenPriceOptionValidatorTests(TestCase):

    def setUp(self):
        self.product = ProductFactory.create()
        self.current_form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "productPrice",
                        "type": "productPrice",
                    }
                ],
            }
        )

        self.text_field_form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "text",
                        "type": "textfield",
                    }
                ],
            }
        )

    def test_multiple_product_price_components_in_single_definition(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "productPrice",
                        "type": "productPrice",
                    },
                    {
                        "key": "productPrice",
                        "type": "productPrice",
                    },
                ],
            }
        )
        with self.assertRaisesMessage(
            ValidationError,
            "Currently only a single product price component is allowed be added to a form.",
        ):
            validate_price_option(None, form_definition, [])

    def test_multiple_product_price_components_in_multiple_definitions(self):
        other_form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "productPrice",
                        "type": "productPrice",
                    }
                ],
            }
        )
        with self.assertRaisesMessage(
            ValidationError,
            "Currently only a single product price component is allowed be added to a form.",
        ):
            validate_price_option(
                None, self.current_form_definition, [other_form_definition]
            )

    def test_product_price_component_without_product_on_form(self):
        with self.assertRaisesMessage(
            ValidationError, "No product has been selected for productPrice component"
        ):
            validate_price_option(None, self.current_form_definition, [])

    def test_product_price_component_with_product_without_options(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Product selected for productPrice component does not have a price from Open Producten",
        ):
            validate_price_option(self.product, self.current_form_definition, [])

    def test_product_price_component_not_required(self):
        PriceFactory.create(product_type=self.product)
        with self.assertRaisesMessage(
            ValidationError, "productPrice component is not currently not required"
        ):
            validate_price_option(self.product, self.current_form_definition, [])

    def test_product_with_only_price_options_without_product_price_component(self):
        product = ProductFactory.create(price=None)
        PriceFactory.create(product_type=product)
        with self.assertRaisesMessage(
            ValidationError,
            "Form has product with only price options but not a productPrice component",
        ):
            validate_price_option(product, self.text_field_form_definition, [])

    def test_valid_definition(self):
        PriceFactory.create(product_type=self.product)
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "productPrice",
                        "type": "productPrice",
                        "validate": {
                            "required": True,
                        },
                    }
                ],
            }
        )
        validate_price_option(self.product, form_definition, [])

    def test_definition_without_product_price_component_and_product(self):
        validate_price_option(None, self.text_field_form_definition, [])

    def test_definition_without_product_price_component_and_product_with_static_price(
        self,
    ):
        product = ProductFactory.create(price="20.00")
        validate_price_option(product, self.text_field_form_definition, [])
