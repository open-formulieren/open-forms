from typing import Literal, TypedDict

from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from rest_framework import serializers

from openforms.authentication.constants import AuthAttribute
from openforms.utils.mixins import JsonSchemaSerializerMixin

from .models import AttributeGroup


class YiviOptions(TypedDict):
    """
    Shape of the DigiD authentication plugin options.

    This describes the shape of :attr:`YiviOptionsSerializer.validated_data`, after
    the input data has been cleaned/validated.
    """

    authentication_options: list[AuthAttribute]
    additional_attributes_groups: list[str]
    bsn_loa: DigiDAssuranceLevels | Literal[""]
    kvk_loa: AssuranceLevels | Literal[""]


class YiviOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    authentication_options = serializers.ListField(
        child=serializers.ChoiceField(
            choices=(
                (AuthAttribute.bsn.value, AuthAttribute.bsn.label),
                (AuthAttribute.kvk.value, AuthAttribute.kvk.label),
                (AuthAttribute.pseudo.value, AuthAttribute.pseudo.label),
            )
        ),
        label=_("Authentication options"),
        help_text=_(
            "Authentication options that can be used by end-users. If left empty, a "
            "pseudo value will be used as identifier."
        ),
        default=list,
        required=False,
        allow_empty=True,
    )
    additional_attributes_groups = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AttributeGroup.objects.annotate(
            str_uuid=Cast("uuid", output_field=CharField())
        ).values_list("str_uuid", flat=True),
        many=True,
        label=_("Additional attributes groups"),
        help_text=_(
            "Additional attributes groups to use for authentication. The end-user can "
            "choose per group whether they provide these attributes or not."
        ),
        default=list,
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

    def _handle_before_import(self, data) -> None:
        # we're not importing, nothing to do
        if not self.context.get("is_import", False):
            return

        # Pre-process 'additional_attributes_groups' before DRF validates it
        attribute_groups = data.get("additional_attributes_groups", [])
        valid_choices = AttributeGroup.objects.all().values_list("name", flat=True)

        # Filter out invalid attribute groups
        data["additional_attributes_groups"] = [
            group for group in attribute_groups if group in valid_choices
        ]

    def to_internal_value(self, data: YiviOptions) -> YiviOptions:
        self._handle_before_import(data)
        return super().to_internal_value(data)
