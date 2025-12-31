from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

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
        profile_form_variable = attrs["profile_form_variable"]
        form = self.context.get("form")

        if form:
            try:
                form_variable = FormVariable.objects.get(
                    form=form, key=profile_form_variable
                )
            except FormVariable.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "profile_form_variable": _(
                            "No form variable with key '{key}' exists in the form."
                        ).format(key=profile_form_variable),
                    }
                )

            component = form_variable.form_definition.configuration_wrapper[
                profile_form_variable
            ]
            if component["type"] != "customerProfile":
                raise serializers.ValidationError(
                    {
                        "profile_form_variable": _(
                            "Only variables of 'profile' components are allowed as "
                            "profile form variable."
                        )
                    }
                )

        return attrs
