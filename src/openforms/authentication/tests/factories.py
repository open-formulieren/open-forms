import factory

from ..constants import AuthAttribute


class AuthInfoFactory(factory.django.DjangoModelFactory):
    plugin = "digid"
    attribute = AuthAttribute.bsn
    value = "123456782"
    machtigen = {}

    class Meta:
        model = "authentication.AuthInfo"
