import factory
from factory.django import DjangoModelFactory
from rest_framework.authtoken.models import Token

from ..models import User


class TokenFactory(DjangoModelFactory):
    user = factory.SubFactory(User)

    class Meta:
        model = Token
