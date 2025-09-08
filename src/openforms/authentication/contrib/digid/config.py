from typing import Literal, TypedDict

from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import DigiDAssuranceLevels
from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin


class DigidOptions(TypedDict):
    """
    Shape of the DigiD authentication plugin options.

    This describes the shape of :attr:`DigidOptionsSerializer.validated_data`, after
    the input data has been cleaned/validated.
    """

    loa: DigiDAssuranceLevels | Literal[""]


class DigidOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    loa = serializers.ChoiceField(
        label=_("options LoA"),
        help_text=_("The minimal LoA for authentication."),
        choices=DigiDAssuranceLevels.choices,
        default="",
        required=False,
        allow_blank=True,
    )
