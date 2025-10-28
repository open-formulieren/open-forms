import factory

from ..constants import HashAlgorithm
from ..models import OgoneMerchant, OgoneWebhookConfiguration


class OgoneMerchantFactory(factory.django.DjangoModelFactory):
    label = "Merchant"
    pspid = "merchant"
    sha_in_passphrase = "sha_in"
    sha_out_passphrase = "sha_out"
    hash_algorithm = HashAlgorithm.sha512

    class Meta:
        model = OgoneMerchant


class OgoneWebhookConfigurationFactory(factory.django.DjangoModelFactory):
    pspid = factory.Sequence(lambda n: f"webhook-{n:03d}")
    webhook_key_id = factory.Faker("pystr", min_chars=20, max_chars=20)
    webhook_key_secret = factory.Faker("pystr", min_chars=128, max_chars=128)

    class Meta:
        model = OgoneWebhookConfiguration
