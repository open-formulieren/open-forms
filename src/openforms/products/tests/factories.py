import factory

from ..models import Product


class ProductFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Product

    name = factory.Faker("word")
    url = factory.Faker("text")
    price = 15.00
