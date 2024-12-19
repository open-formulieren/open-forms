from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.models import Service

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.utils.mixins import JsonSchemaSerializerMixin


class JSONOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    service = PrimaryKeyRelatedAsChoicesField(
        queryset=Service.objects.all(),
        label=_("Service"),
        help_text=_("Which service to use."),
    )
    # TODO-4098: show the complete API endpoint as a (tooltip) hint after user entry? Might be a front-end thing...
    relative_api_endpoint = serializers.CharField(
        max_length=255,
        label=_("Relative API endpoint"),
        help_text=_("The API endpoint to send the data to (relative to the service API root)."),
        allow_blank=True,
    )
    form_variables = serializers.ListField(
        child=FormioVariableKeyField(max_length=50),
        label=_("Form variable key list"),
        help_text=_(
            "A comma-separated list of form variables (can also include static variables) to use."
        )
    )
