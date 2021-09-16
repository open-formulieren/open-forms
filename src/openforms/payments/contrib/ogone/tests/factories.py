import factory

from ..constants import HashAlgorithm
from ..models import OgoneMerchant


class OgoneMerchantFactory(factory.django.DjangoModelFactory):
    label = "Merchant"
    pspid = "merchant"
    sha_in_passphrase = "sha_in"
    sha_out_passphrase = "sha_out"
    hash_algorithm = HashAlgorithm.sha512

    class Meta:
        model = OgoneMerchant
