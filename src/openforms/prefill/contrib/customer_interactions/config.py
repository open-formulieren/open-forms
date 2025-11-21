from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.fields import SlugRelatedAsChoicesField
from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.utils.mixins import JsonSchemaSerializerMixin


class CommunicationPreferencesSerializer(
    JsonSchemaSerializerMixin, serializers.Serializer
):
    customer_interactions_api_group = SlugRelatedAsChoicesField(
        queryset=CustomerInteractionsAPIGroupConfig.objects.all(),
        slug_field="identifier",
        label=_("Customer Interactions API group"),
        required=True,
        help_text=_("Which Customer Interactions API group to use."),
    )
    profile_form_variable = FormioVariableKeyField(
        label=_("Profile form variable key"),
        help_text=_(
            "The 'dotted' path to a form variable key of a customer-profile component. "
            "The format should comply to how Formio handles nested component keys."
        ),
    )
