from django.db import models, transaction

import openforms.contrib.open_producten.api_models as api_models
from openforms.contrib.open_producten.models import Price, PriceOption
from openforms.products.models import Product as ProductType


class PriceImporter:

    def __init__(self, client):
        self.client = client
        self.created_objects = []
        self.updated_objects = []
        self.product_types = []

    def _add_to_log_list(self, instance: models.Model, created: bool):
        if created:
            self.created_objects.append(instance)
        else:
            self.updated_objects.append(instance)

    @transaction.atomic()
    def import_product_types(self):

        self.product_types = self.client.get_current_prices()
        self._handle_product_types(self.product_types)
        return (
            self.created_objects,
            self.updated_objects,
        )

    def _handle_options(self, options: [api_models.PriceOption], price_instance: Price):
        for option in options:
            option_instance, created = PriceOption.objects.update_or_create(
                uuid=option.id,
                defaults={
                    "amount": option.amount,
                    "description": option.description,
                    "price": price_instance,
                },
            )
            self._add_to_log_list(option_instance, created)

    def _update_or_create_price(self, price: api_models.Price, product_type_instance):
        price_instance, created = Price.objects.update_or_create(
            uuid=price.id,
            defaults={
                "valid_from": price.valid_from,
                "product_type": product_type_instance,
            },
        )
        self._add_to_log_list(price_instance, created)
        return price_instance

    def _handle_product_types(self, product_types: list[api_models.ProductType]):
        for product_type in product_types:

            product_type_instance, created = ProductType.objects.update_or_create(
                uuid=product_type.id,
                defaults={
                    "name": product_type.name,
                    "upl_uri": product_type.upl_uri,
                    "upl_name": product_type.upl_name,
                },
            )
            self._add_to_log_list(product_type_instance, created)

            if product_type.current_price:
                price_instance = self._update_or_create_price(
                    product_type.current_price, product_type_instance
                )
                self._handle_options(product_type.current_price.options, price_instance)
