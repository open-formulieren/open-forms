from datetime import datetime

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.request import Request

from openforms.forms.models import Form
from openforms.frontend import get_frontend_redirect_url
from openforms.submissions.models import Submission

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
    redirect_url = serializers.SerializerMethodField(
        label=_("Redirect URL"),
        read_only=True,
        help_text=_(
            "URL to send the form submitter to, which will start the form submission "
            "with the specified initial data/context. If `formUrl` was provided, the "
            "resulting URL is based on it, otherwise the internal pages are used."
        ),
    )
    expires_at = serializers.SerializerMethodField(
        label=_("Expires at"),
        read_only=True,
        help_text=_(
            "Timestamp when this initial data will no longer be usable. It's "
            "calculated from the creation timestamp + the provided TTL."
        ),
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = InitialSubmissionData
        fields = (
            "uuid",
            "form",
            "form_url",
            "representee",
            "ttl",
            "redirect_url",
            "expires_at",
        )
        extra_kwargs = {
            "uuid": {"read_only": True},
            "form_url": {"write_only": True},
            "ttl": {"write_only": True},
        }

    @extend_schema_field(OpenApiTypes.URI)
    def get_redirect_url(self, obj: InitialSubmissionData) -> str:
        request: Request = self.context["request"]
        base_url = obj.form_url or request.build_absolute_uri(
            reverse("core:form-detail", kwargs={"slug": obj.form.slug})
        )
        temp_submission = Submission(form=obj.form, form_url=base_url)
        return get_frontend_redirect_url(
            temp_submission,
            action="init",
            action_params={"representee_ref": str(obj.uuid)},
        )

    def get_expires_at(self, obj: InitialSubmissionData) -> datetime:
        return obj.expiry_date
