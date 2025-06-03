from typing import List, Literal, TypedDict

from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin

from .constants import YiviAuthenticationAttributes
from .models import AttributeGroup


class YiviOptions(TypedDict):
    """
    Shape of the DigiD authentication plugin options.
    This describes the shape of :attr:`YiviOptionsSerializer.validated_data`, after
    the input data has been cleaned/validated.
    """

    authentication_options: List[YiviAuthenticationAttributes]
    additional_attributes_groups: List[str]
    bsn_loa: DigiDAssuranceLevels | Literal[""] | None
    kvk_loa: AssuranceLevels | Literal[""] | None


class YiviOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    authentication_options = serializers.ListField(
        child=serializers.ChoiceField(choices=YiviAuthenticationAttributes.choices),
        label=_("Authentication options"),
        help_text=_(
            "Authentication options that can be used by end-users. The pseudo option "
            "makes this field optional. If left empty, a pseudo value will be used as "
            "identifier."
        ),
        default=[],
        required=False,
        allow_empty=True,
    )
    additional_attributes_groups = serializers.ListField(
        child=serializers.ChoiceField(choices=[]),  # Choices are dynamically defined
        label=_("Additional attributes groups"),
        help_text=_(
            "Additional attributes groups to use for authentication. The end-user can "
            "choice per group whether they provide these attributes or not."
        ),
        default=[],
        required=False,
        allow_empty=True,
    )

    bsn_loa = serializers.ChoiceField(
        label=_("options bsn LoA"),
        help_text=_("The minimal LoA for bsn authentication."),
        choices=DigiDAssuranceLevels.choices,
        default=DigiDAssuranceLevels.middle,
        required=False,
        allow_blank=True,
    )
    kvk_loa = serializers.ChoiceField(
        label=_("options kvk LoA"),
        help_text=_("The minimal LoA for kvk authentication."),
        choices=AssuranceLevels.choices,
        default=AssuranceLevels.substantial,
        required=False,
        allow_blank=True,
    )

    def get_fields(self):
        fields = super().get_fields()
        view = self.context.get("view")
        if getattr(view, "swagger_fake_view", False):
            return fields

        fields["additional_attributes_groups"].child.choices = list(
            AttributeGroup.objects.all().values_list("name", "description")
        )
        return fields
