from typing import TypedDict

from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import DigiDAssuranceLevels
from rest_framework import serializers
from typing_extensions import NotRequired

from openforms.utils.mixins import JsonSchemaSerializerMixin


class LoAOptions(TypedDict):
    loa: NotRequired[str]


class LoAOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    loa = serializers.ChoiceField(
        label=_("options LoA"),
        help_text=_("The minimal LoA for authentication."),
        choices=DigiDAssuranceLevels.choices,
        default=DigiDAssuranceLevels.middle,
        required=False,
        allow_blank=True,
    )
