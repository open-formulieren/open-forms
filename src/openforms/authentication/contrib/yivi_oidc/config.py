from typing import List, Literal, TypedDict

from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import DigiDAssuranceLevels
from drf_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin

from .constants import YiviAuthenticationAttributes
from .models import AvailableScope


class YiviOptions(TypedDict):
    """
    Shape of the DigiD authentication plugin options.

    This describes the shape of :attr:`YiviOptionsPolymorphicSerializer.validated_data`, after
    the input data has been cleaned/validated.
    """

    authentication_attribute: YiviAuthenticationAttributes
    additional_scopes: List[str]
    loa: DigiDAssuranceLevels | Literal[""] | None


class YiviPseudoOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


class YiviKvkOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


class YiviBSNOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    loa = serializers.ChoiceField(
        label=_("options LoA"),
        help_text=_("The minimal LoA for authentication."),
        choices=DigiDAssuranceLevels.choices,
        default=DigiDAssuranceLevels.middle,
        required=False,
        allow_blank=True,
    )


class YiviOptionsPolymorphicSerializer(
    JsonSchemaSerializerMixin, PolymorphicSerializer, serializers.Serializer
):
    authentication_attribute = serializers.ChoiceField(
        label=_("Authentication attribute"),
        help_text=_("The authentication attribute that will be fetched."),
        choices=YiviAuthenticationAttributes.choices,
        required=True,
    )
    additional_scopes = serializers.ListField(
        child=serializers.ChoiceField(choices=[]),  # Choices are dynamically defined
        label=_("Additional scopes"),
        help_text=_("Additional scopes to use for authentication."),
        default=[],
        required=False,
        allow_empty=True,
    )

    discriminator_field = "authentication_attribute"
    serializer_mapping = {
        YiviAuthenticationAttributes.bsn: YiviBSNOptionsSerializer,
        YiviAuthenticationAttributes.kvk: YiviKvkOptionsSerializer,
        YiviAuthenticationAttributes.pseudo: YiviPseudoOptionsSerializer,
    }

    def get_fields(self):
        fields = super().get_fields()
        fields[
            "additional_scopes"
        ].child.choices = AvailableScope.objects.all().values_list(
            "scope", "description"
        )
        return fields
