from typing import TypedDict

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin


class PrefillAttributeChoice(TypedDict):
    label: str
    value: str


class YiviPrefillAttributeApiResponse(TypedDict):
    attribute_group_uuid: str
    attributes: list[PrefillAttributeChoice]
    is_static: bool


class PrefillAttributeChoiceSerializer(serializers.Serializer):
    label = serializers.CharField(
        label=_("Label"),
        help_text=_("Prefill attribute label"),
        default="",
    )
    value = serializers.CharField(
        label=_("Value"),
        help_text=_("Prefill attribute value"),
        default="",
    )


class YiviPrefillAttributeSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    attribute_group_uuid = serializers.UUIDField(
        label=_("Attribute group UUID"),
        help_text=_("The UUID of the related attribute group."),
    )
    attributes = serializers.ListField(
        child=PrefillAttributeChoiceSerializer(),
        label=_("Prefill attributes"),
        help_text=_(
            "Prefill attributes derived from the attribute group with uuid"
            "`attribute_group_uuid`. The `attributes` should only be used for prefill, if"
            "the corresponding Yivi attribute group is used in the authentication"
            "backend."
        ),
        default=list(),
    )
    is_static = serializers.BooleanField(
        label=_("Is static"),
        help_text=_(
            "Static prefill attributes aren't related to any attribute groups, and can"
            "always be used for Yivi prefill."
        ),
        default=False,
    )
