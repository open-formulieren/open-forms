from dataclasses import dataclass
from typing import Callable

from django.utils.translation import gettext_lazy as _

from djangorestframework_camel_case.util import underscoreize
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers

from openforms.api.utils import underscore_to_camel
from openforms.plugins.api.serializers import PluginBaseSerializer

from ..base import BasePlugin


class PrefillPluginSerializer(PluginBaseSerializer):
    requires_auth = serializers.CharField(
        label=_("Required authentication attribute"),
        help_text=_(
            "The authentication attribute required for this plugin to lookup remote data."
        ),
        allow_null=True,
    )


PrefillPluginPredicate = Callable[[BasePlugin], bool]


class PrefillPluginPredicateSerializer(serializers.Serializer[PrefillPluginPredicate]):
    component_type = serializers.CharField(
        required=False,
        label=_("Form.io component type"),
        help_text=_("Only return plugins applicable for the specified component type."),
    )

    def to_internal_value(self, data):
        return super().to_internal_value(underscoreize(data))

    def save(self, **_kwargs) -> PrefillPluginPredicate:
        # We don't "save" anything, just create and return a predicate function
        # save is a weird name in this context, but Serializers weren't designed with deserializing
        # query string parameters in mind.
        # https://www.django-rest-framework.org/api-guide/serializers/#overriding-save-directly

        match self.validated_data:
            case {"component_type": component_type} if component_type:
                return lambda plugin: component_type in plugin.for_components
            case _:
                # all plugins
                return lambda _: True

    @classmethod
    def as_openapi_params(cls) -> list[OpenApiParameter]:
        # FIXME: See openforms.validators.api.serializers.ValidatorsFilterSerializer
        instance = cls()
        ct_field = instance.fields["component_type"]
        return [
            OpenApiParameter(
                underscore_to_camel(str(ct_field.field_name)),
                OpenApiTypes.STR,
                description=str(ct_field.help_text),
            )
        ]


@dataclass
class ChoiceWrapper:
    choice: tuple

    def __post_init__(self):
        self.value = self.choice[0]
        self.label = self.choice[1]


class PrefillAttributeSerializer(serializers.Serializer):
    id = serializers.CharField(
        source="value",
        label=_("ID"),
        help_text=_("The unique attribute identifier"),
    )
    label = serializers.CharField(
        label=_("Label"),
        help_text=_("The human-readable name for an attribute."),
    )
