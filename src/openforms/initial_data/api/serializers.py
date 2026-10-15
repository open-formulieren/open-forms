from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.forms.models import Form

from ..constants import SupportedAuthAttributes
from ..models import InitialSubmissionData


class RepresenteeSerializer(serializers.ModelSerializer):
    # TODO: run BSN/KVK number validation based on the specified auth attribute
    # TODO: validate that the auth attribute makes sense in the context of the form? not
    # sure we can do this actually, with the loose coupling we have...
    auth_attribute = serializers.ChoiceField(
        source="representee_auth_attribute",
        choices=SupportedAuthAttributes.choices,
        label=_("Authentication attribute"),
        help_text=_(
            "Attribute that will be provided for the submission authentication."
        ),
    )
    value = serializers.CharField(
        source="representee_auth_value",
        label=_("identifier"),
        help_text=_("Value of the identifier for the submission authentication."),
        max_length=250,
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = InitialSubmissionData
        fields = ("auth_attribute", "value")


class InitialSubmissionDataSerializer(serializers.ModelSerializer):
    form = serializers.SlugRelatedField(
        queryset=Form.objects.live(),
        slug_field="uuid",
        label=_("Form to start"),
        help_text=_("UUID of the form about to be started."),
        write_only=True,
    )
    representee = RepresenteeSerializer(
        source="*",
        required=True,
        write_only=True,
        label=_("representee"),
        help_text=_(
            "Identification details for the representee on whose behalf the form is "
            "about to be filled out."
        ),
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = InitialSubmissionData
        fields = (
            "form",
            "form_url",
            "representee",
            "ttl",
        )
        extra_kwargs = {
            "form_url": {"write_only": True},
            "ttl": {"write_only": True},
        }
