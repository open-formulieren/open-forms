from datetime import datetime, timedelta
from typing import NotRequired, TypedDict, assert_never

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from rest_framework.fields import get_error_detail
from rest_framework.request import Request

from openforms.contrib.kvk.validators import validate_branchNumber, validate_kvk
from openforms.forms.models import Form
from openforms.frontend import get_frontend_redirect_url
from openforms.submissions.models import Submission
from openforms.utils.validators import validate_bsn

from ..constants import SupportedAuthAttributes
from ..models import InitialSubmissionData


class RepresenteeData(TypedDict):
    representee_auth_attribute: str
    representee_auth_value: str
    representee_branch_number: NotRequired[str]


class RepresenteeSerializer(serializers.Serializer):
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
    # preferably I'd use PolymorphicSerializer for this instead, but there's a bug in
    # how the (empty) validated data is interpreted - see
    # https://github.com/maykinmedia/drf-polymorphic/issues/15
    branch_number = serializers.CharField(
        source="representee_branch_number",
        required=False,
        allow_blank=True,
        label=_("KvK branch number"),
        help_text=_(
            "Optional branch number of the company identified by KVK. Note that this "
            "may only be provided if the auth attribute is 'kvk'."
        ),
    )

    def validate(self, attrs: RepresenteeData) -> RepresenteeData:
        attrs = super().validate(attrs)

        attribute = SupportedAuthAttributes(attrs["representee_auth_attribute"])
        value = attrs["representee_auth_value"]
        branch_number = attrs.get("representee_branch_number", "")

        errors: dict[str, list[ErrorDetail] | ErrorDetail] = {}

        match attribute:
            case SupportedAuthAttributes.bsn:
                value_validator = validate_bsn
            case SupportedAuthAttributes.kvk:
                value_validator = validate_kvk
                if branch_number:
                    try:
                        validate_branchNumber(branch_number)
                    except ValidationError as exc:
                        errors["branch_number"] = get_error_detail(exc)
            case _:  # pragma: no cover
                assert_never(attribute)

        try:
            value_validator(value)
        except ValidationError as exc:
            errors["value"] = get_error_detail(exc)

        if branch_number and attribute != SupportedAuthAttributes.kvk:
            errors["branch_number"] = ErrorDetail(
                gettext("You may only provide a branch number for KvK attributes."),
                code="invalid",
            )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


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
    ttl = serializers.IntegerField(
        label=_("ttl (in hours)"),
        required=True,
        help_text=_(
            "Time-to-live in hours. The expiry date is calculated from the creation "
            "timestamp plus the TTL. After this moment, the submission data will be "
            "deleted. A submission should be started within this TTL."
        ),
        min_value=1,
        max_value=24,
        write_only=True,
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

    def save(self, **kwargs) -> InitialSubmissionData:
        # transform ttl int in hours to proper duration
        ttl_hours = self.validated_data["ttl"]
        kwargs["ttl"] = timedelta(hours=ttl_hours)
        return super().save(**kwargs)
