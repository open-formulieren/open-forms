from decimal import Decimal

import factory

from ..models import Product


class ProductFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    price = Decimal("15.00")

    class Meta:
        model = Product
