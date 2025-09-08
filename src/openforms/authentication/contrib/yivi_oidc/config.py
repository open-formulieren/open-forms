from collections.abc import Sequence
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
    additional_attributes_groups: Sequence[AttributeGroup]
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
        queryset=AttributeGroup.objects.all(),
        slug_field="uuid",
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

        attribute_groups = data.get("additional_attributes_groups", [])
        if not attribute_groups:
            return

        attribute_groups_map = dict(AttributeGroup.objects.values_list("name", "uuid"))

        # If we encounter an attribute_group that uses the old notation (attribute_group
        # name as identifier) and we have an attributeGroup with the same name, we use
        # the uuid of that known attributeGroup as identifier.
        # Otherwise, we just use the imported data
        data["additional_attributes_groups"] = [
            group
            if group not in attribute_groups_map
            else str(attribute_groups_map[group])
            for group in attribute_groups
        ]

    def to_internal_value(self, data: YiviOptions) -> YiviOptions:
        self._handle_before_import(data)
        return super().to_internal_value(data)
