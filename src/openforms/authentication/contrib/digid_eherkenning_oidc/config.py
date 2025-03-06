from typing import TypedDict

from rest_framework import serializers

from openforms.authentication.config import LoAOptions, LoAOptionsSerializer
from openforms.utils.mixins import JsonSchemaSerializerMixin


class DigiDOIDCOptions(LoAOptions, TypedDict):
    """
    Shape of the DigiD OIDC authentication plugin options.

    This describes the shape of :attr:`DigiDOIDCOptionsSerializer.validated_data`, after
    the input data has been cleaned/validated.
    """


class DigiDOIDCOptionsSerializer(
    LoAOptionsSerializer, JsonSchemaSerializerMixin, serializers.Serializer
):
    pass
