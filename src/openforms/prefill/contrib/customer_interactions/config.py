from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from formio_types import CustomerProfile
from openforms.api.fields import SlugRelatedAsChoicesField
from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.forms.models import FormVariable
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

    def validate(self, attrs):
        variable_key = attrs["profile_form_variable"]
        form = self.context.get("form")

        if form:
            try:
                form_variable = FormVariable.objects.get(form=form, key=variable_key)
            except FormVariable.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "profile_form_variable": _(
                            "No form variable with key '{key}' exists in the form."
                        ).format(key=variable_key),
                    }
                )

            component = form_variable.form_definition.formio_config[variable_key]
            if not isinstance(component, CustomerProfile):
                raise serializers.ValidationError(
                    {
                        "profile_form_variable": _(
                            "Only variables of 'profile' components are allowed as "
                            "profile form variable."
                        )
                    }
                )

        return attrs
