import factory

from ..models import WorldlineMerchant


class WorldlineMerchantFactory(factory.django.DjangoModelFactory):
    label = "Merchant"
    pspid = "merchant"
    api_key = "key"
    api_secret = "sekrit"

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = WorldlineMerchant
