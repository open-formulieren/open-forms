from django.utils.translation import gettext_lazy as _

from djangorestframework_camel_case.util import underscoreize
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers

from openforms.api.utils import underscore_to_camel


class ValidationInputSerializer(serializers.Serializer):
    submission_uuid = serializers.UUIDField(
        label=_("Submission UUID"),
        help_text=_("UUID of the submission."),
    )


class ValidatorsFilterSerializer(serializers.Serializer):
    component_type = serializers.CharField(
        required=False,
        label=_("Form.io component type"),
        help_text=_(
            "Only return validators applicable for the specified component type."
        ),
        allow_blank=True,
    )

    def to_internal_value(self, data):
        return super().to_internal_value(underscoreize(data))

    @classmethod
    def as_openapi_params(cls) -> list[OpenApiParameter]:
        # FIXME: this should be solved as an extension instead, but at least it's now
        # kept together
        instance = cls()
        ct_field = instance.fields["component_type"]
        name = ct_field.field_name
        assert name
        return [
            OpenApiParameter(
                underscore_to_camel(name),
                OpenApiTypes.STR,
                description=ct_field.help_text or "",
            )
        ]


class ValidationResultSerializer(serializers.Serializer):
    is_valid = serializers.BooleanField(  # pyright: ignore[reportAssignmentType]
        label=_("Is valid"), help_text=_("Boolean indicating value passed validation.")
    )
    messages = serializers.ListField(
        child=serializers.CharField(
            label=_("error message"),
            help_text=_("error message"),
        ),
        help_text=_("List of validation error messages for display."),
    )


class ValidationPluginSerializer(serializers.Serializer):
    id = serializers.CharField(
        source="identifier",
        label=_("ID"),
        help_text=_("The unique plugin identifier"),
    )
    label = serializers.CharField(  # pyright: ignore[reportAssignmentType]
        source="verbose_name",
        label=_("Label"),
        help_text=_("The human-readable name for a plugin."),
    )
    for_components = serializers.ListField(
        label=_("Components"),
        help_text=_("The components for which the plugin is relevant."),
        child=serializers.CharField(),
    )
