from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.models import Service

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.utils.mixins import JsonSchemaSerializerMixin


class JSONOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    # TODO-4098: is service enough, or do we need an API group like the ObjectsAPI?
    service = PrimaryKeyRelatedAsChoicesField(
        queryset=Service.objects.all(),
        label=_("Service"),
        help_text=_("Which service to use."),
    )
    # TODO-4098: show the complete API endpoint as a (tooltip) hint after user entry?
    relative_api_endpoint = serializers.CharField(
        max_length=255,
        label=_("Relative API endpoint"),
        help_text=_("The API endpoint to send the data to (relative to the service API root)."),
    )
    # TODO-4098: should be linked to the checkboxes in the form variable table
    # TODO-4098: is it possible to have a choices field of variable keys, where you can select them
    #  from a drop-down list?
    form_variables = serializers.ListField(
        child=FormioVariableKeyField(max_length=50),
        label=_("Form variable key list"),
        help_text=_(
            "A comma-separated list of form variables (can also include static variables) to use."
        )
    )
