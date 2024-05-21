import logging
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import elasticapm
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from csp_post_processor.drf.fields import CSPPostProcessedHTMLField
from openforms.api.utils import mark_experimental
from openforms.config.models import GlobalConfiguration
from openforms.emails.utils import render_email_template, send_mail_html
from openforms.formio.service import build_serializer
from openforms.formio.utils import iter_components
from openforms.forms.api.serializers import FormDefinitionSerializer
from openforms.forms.constants import SubmissionAllowedChoices
from openforms.forms.models import FormStep
from openforms.forms.validators import validate_not_deleted
from openforms.utils.urls import build_absolute_uri

from ..attachments import validate_uploads
from ..constants import ProcessingResults, ProcessingStatuses
from ..form_logic import check_submission_logic, evaluate_form_logic
from ..models import Submission, SubmissionStep
from ..tokens import submission_resume_token_generator
from ..utils import get_report_download_url
from .fields import (
    NestedRelatedField,
    PrivacyPolicyAcceptedField,
    TruthDeclarationAcceptedField,
)
from .validators import FormMaintenanceModeValidator, ValidatePrefillData

logger = logging.getLogger(__name__)


class NestedSubmissionStepSerializer(NestedHyperlinkedModelSerializer):
    id = serializers.UUIDField(source="form_step.uuid")
    name = serializers.CharField(source="form_step.form_definition.name")

    url = NestedRelatedField(
        view_name="api:submission-steps-detail",
        source="*",
        read_only=True,
        lookup_field="form_step__uuid",
        lookup_url_kwarg="step_uuid",
        parent_lookup_kwargs={
            "submission_uuid": "submission__uuid",
        },
    )

    form_step = NestedRelatedField(
        view_name="api:form-steps-detail",
        source="*",
        read_only=True,
        lookup_field="form_step__uuid",
        lookup_url_kwarg="uuid",
        parent_lookup_kwargs={
            "form_uuid_or_slug": "submission__form__uuid",
        },
    )

    class Meta:
        model = SubmissionStep
        fields = (
            "id",
            "name",
            "url",
            "form_step",
            "is_applicable",
            "completed",
            "can_submit",
        )


class NestedSubmissionPaymentDetailSerializer(serializers.ModelSerializer):
    is_required = serializers.BooleanField(
        label=_("payment required"),
        help_text=_("Whether the registration requires payment."),
        read_only=True,
        source="payment_required",
    )
    has_paid = serializers.BooleanField(
        label=_("user has paid"),
        source="payment_user_has_paid",
        help_text=_("Whether the user has completed the required payment."),
        read_only=True,
    )
    amount = serializers.DecimalField(
        label=_("payment amount"),
        # from Submission model
        max_digits=10,
        decimal_places=2,
        source="price",
        help_text=_("Amount (to be) paid"),
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Submission
        fields = (
            "is_required",
            "amount",
            "has_paid",
        )


class SubmissionSerializer(serializers.HyperlinkedModelSerializer):
    steps = NestedSubmissionStepSerializer(
        label=_("Submission steps"),
        read_only=True,
        many=True,
        help_text=_(
            "Details of every form step of this submission's form, tracking the "
            "progress and other meta-data of each particular step."
        ),
    )
    submission_allowed = serializers.ChoiceField(
        choices=SubmissionAllowedChoices.choices,
        label=_("submission allowed"),
        source="form.submission_allowed",
        help_text=_(
            "Whether the user is allowed to submit this form and whether the user should see the overview page."
        ),
        required=False,
        read_only=True,
    )

    payment = NestedSubmissionPaymentDetailSerializer(
        label=_("payment information"),
        source="*",
        read_only=True,
    )

    is_authenticated = serializers.BooleanField(
        label=_("is authenticated"),
        help_text=_(
            "Whether the user was authenticated when creating this submission."
        ),
        read_only=True,
    )

    class Meta:
        model = Submission
        fields = (
            "id",
            "url",
            "form",
            "steps",
            "submission_allowed",
            "is_authenticated",
            "payment",
            "form_url",
        )
        extra_kwargs = {
            "id": {
                "read_only": True,
                "source": "uuid",
            },
            "url": {
                "view_name": "api:submission-detail",
                "lookup_field": "uuid",
            },
            "form": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
                "validators": [
                    FormMaintenanceModeValidator(),
                    validate_not_deleted,
                ],
            },
            "form_url": {
                "required": True,
            },
        }

    def to_representation(self, instance):
        check_submission_logic(instance, unsaved_data=self.context.get("unsaved_data"))
        return super().to_representation(instance)


class ContextAwareFormStepSerializer(serializers.ModelSerializer):
    configuration = serializers.SerializerMethodField()

    class Meta:
        model = FormStep
        fields = ("index", "configuration")
        extra_kwargs = {
            "index": {"source": "order"},
        }

    @elasticapm.capture_span(span_type="app.api.serialization")
    def get_configuration(self, instance) -> dict:
        submission = self.root.instance.submission
        serializer = FormDefinitionSerializer(
            instance=instance.form_definition,
            context={**self.context, "submission": submission},
        )
        return serializer.data["configuration"]


class SubmissionStepSerializer(NestedHyperlinkedModelSerializer):
    form_step = ContextAwareFormStepSerializer(read_only=True)
    slug = serializers.SlugField(source="form_step.slug", read_only=True)
    data = serializers.DictField(  # type: ignore
        label=_("data"),
        required=False,
        allow_null=True,
        validators=[ValidatePrefillData()],
    )

    parent_lookup_kwargs = {
        "submission_uuid": "submission__uuid",
    }

    instance: SubmissionStep

    class Meta:
        model = SubmissionStep
        fields = (
            "id",
            "slug",
            "form_step",
            "data",
            "is_applicable",
            "completed",
            "can_submit",
        )

        extra_kwargs = {
            "id": {
                "read_only": True,
                "source": "uuid",
                "allow_null": True,
            },
        }

    @elasticapm.capture_span(span_type="app.api.serialization")
    def to_representation(self, instance):
        # invoke the configured form logic to dynamically update the Formio.js configuration
        new_configuration = evaluate_form_logic(
            instance.submission,
            instance,
            instance.submission.data,
            **self.context,
        )
        # update the config for serialization
        instance.form_step.form_definition.configuration = new_configuration
        return super().to_representation(instance)

    def validate_data(self, data: dict):
        validate_uploads(self.instance, data=data)
        self._run_formio_validation(data)
        return data

    def _run_formio_validation(self, data: dict) -> None:
        from ..form_logic import evaluate_form_logic

        # Check feature flag to opt out of formio validation first.
        config = GlobalConfiguration.get_solo()
        assert isinstance(config, GlobalConfiguration)
        if not config.enable_backend_formio_validation:
            return

        submission = self.instance.submission
        # evaluate dynamic configuration
        configuration = evaluate_form_logic(submission, step=self.instance, data=data)

        # mark them all as not required
        for component in iter_components(configuration):
            if "validate" not in component:
                continue
            if not component["validate"].get("required", False):
                continue
            component["validate"]["required"] = False

        step_data_serializer = build_serializer(
            configuration["components"],
            data=data,
            context={"submission": submission},
        )
        step_data_serializer.is_valid(raise_exception=True)


class FormDataSerializer(serializers.Serializer):
    data = serializers.DictField(
        label=_("form data"),
        required=False,
        help_text=_(
            "The Form.io submission data object. This will be merged with the full "
            "form submission data, including data from other steps, to evaluate the "
            "configured form logic."
        ),
    )


class SubmissionSuspensionSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        write_only=True,
        label=_("Contact email address"),
        help_text=_(
            "The email address where the 'magic' resume link should be sent to"
        ),
    )

    class Meta:
        model = Submission
        fields = (
            "email",
            "suspended_on",
        )
        extra_kwargs = {
            "suspended_on": {
                "read_only": True,
            }
        }

    def update(self, instance, validated_data):
        email = validated_data.pop("email")
        instance.suspended_on = timezone.now()
        if instance.is_authenticated:
            instance.auth_info.hash_identifying_attributes()
        instance = super().update(instance, validated_data)
        transaction.on_commit(lambda: self.notify_suspension(instance, email))
        return instance

    def get_continue_url(self, instance: Submission) -> str:
        token = submission_resume_token_generator.make_token(instance)

        continue_path = reverse(
            "submissions:resume",
            kwargs={
                "token": token,
                "submission_uuid": instance.uuid,
            },
        )
        return build_absolute_uri(continue_path, request=self.context.get("request"))

    def notify_suspension(self, instance: Submission, email: str):
        continue_url = self.get_continue_url(instance)

        config = GlobalConfiguration.get_solo()
        days_until_removal = (
            instance.form.incomplete_submissions_removal_limit
            or config.incomplete_submissions_removal_limit
        )
        datetime_removed = instance.created_on + timedelta(days=days_until_removal)

        context = {
            "form_name": instance.form.name,
            "save_date": timezone.now(),
            "expiration_date": datetime_removed,
            "continue_url": continue_url,
        }

        send_mail_html(
            render_email_template(config.save_form_email_subject, context),
            render_email_template(config.save_form_email_content, context),
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )


class SubmissionStateLogicSerializer(serializers.Serializer):
    submission = SubmissionSerializer()
    step = SubmissionStepSerializer()


@dataclass
class SubmissionStateLogic:
    submission: Submission
    step: SubmissionStep | None = None


class SubmissionCompletionSerializer(serializers.Serializer):
    status_url = serializers.URLField(
        label=_("status check endpoint"),
        help_text=_(
            "The API endpoint where the background processing status can be checked. "
            "After calling the completion endpoint, this status URL should be polled "
            "to report the processing status back to the end-user. Note that the "
            "endpoint contains a token which invalidates on state changes and after "
            "one day."
        ),
    )


class SubmissionProcessingStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        label=_("background processing status"),
        choices=ProcessingStatuses.choices,
        default=ProcessingStatuses.in_progress,
        help_text=_(
            "The async task state, managed by the async task queue. Once the status is "
            "`done`, check the `result` field for the outcome."
        ),
    )
    result = serializers.ChoiceField(
        label=_("background processing result"),
        choices=ProcessingResults.choices,
        required=False,
        allow_blank=True,
        help_text=_(
            "The result from the background processing. This field only has a value "
            "if the processing has completed (both successfully or with errors)."
        ),
    )

    # error states
    error_message = serializers.CharField(
        label=_("Error information"),
        required=False,
        allow_blank=True,
        help_text=_(
            "Error feedback in case the processing did not complete successfully."
        ),
    )

    # success states
    public_reference = serializers.CharField(
        label=_("Public reference"),
        source="submission.public_registration_reference",
        required=False,
        allow_blank=True,
        help_text=_(
            "The public registration reference, sourced from the registration backend "
            "or otherwise uniquely generated in case the backend could not provide it."
        ),
    )

    confirmation_page_content = CSPPostProcessedHTMLField(
        label=_("Confirmation page content"),
        required=False,
        help_text=_("Body text of the confirmation page. May contain HTML!"),
    )
    report_download_url = serializers.URLField(
        label=_("Report download URL"),
        required=False,
        allow_blank=True,
        help_text=_(
            "Download URL for the generated PDF report. Note that this contain "
            "a timestamped token generated by the backend."
        ),
    )
    payment_url = serializers.URLField(
        label=_("Payment URL"),
        required=False,
        allow_blank=True,
        help_text=_(
            "URL to retrieve the payment information. Note that this (will) contain(s) "
            "a timestamped token generated by the backend."
        ),
    )
    main_website_url = serializers.SerializerMethodField()

    def get_main_website_url(self, obj) -> str:
        if not obj.submission.form.display_main_website_link:
            return ""
        return GlobalConfiguration.get_solo().main_website


class SubmissionCoSignStatusSerializer(serializers.ModelSerializer):
    co_signed = serializers.SerializerMethodField(
        label=_("is co-signed?"),
        help_text=_("Indicator whether the submission has been co-signed or not."),
    )
    representation = serializers.SerializerMethodField(
        label=_("Co-signer display"),
        help_text=_("Co-signer representation string for the UI."),
    )

    class Meta:
        model = Submission
        fields = ("co_signed", "representation")

    def get_co_signed(self, submission: Submission) -> bool:
        co_sign_data = submission.co_sign_data
        return bool(co_sign_data.get("plugin") and co_sign_data.get("identifier"))

    def get_representation(self, submission: Submission) -> str:
        return submission.co_sign_data.get("representation", "")


class SubmissionComponentSummarySerializer(serializers.Serializer):
    name = serializers.CharField(
        help_text=_("Display name of the component."),
        required=True,
    )
    value = serializers.JSONField(
        help_text=_("Raw value of the component."),
        required=True,
    )
    component = serializers.DictField(
        help_text=_("Configuration of the component."),
        required=True,
    )


class SubmissionStepSummarySerialzier(serializers.Serializer):
    slug = serializers.SlugField(
        help_text=_("Slug of the form definition used in the form step."),
        required=True,
    )
    name = serializers.CharField(
        help_text=_("Name of the form definition used in the form step."),
        required=True,
    )
    data = SubmissionComponentSummarySerializer(many=True)


@mark_experimental
class CosignValidationSerializer(serializers.Serializer):
    privacy_policy_accepted = PrivacyPolicyAcceptedField(
        label=_("privacy policy accepted"),
        help_text=_("Whether the co-signer has accepted the privacy policy"),
    )
    statement_of_truth_accepted = TruthDeclarationAcceptedField(
        label=_("statement of truth accepted"),
        help_text=_(
            "Whether the co-signer has declared the form to be filled out truthfully."
        ),
        default=False,
    )

    def save(self, **kwargs):
        submission: Submission = self.context["submission"]
        submission.cosign_complete = True
        submission.cosign_privacy_policy_accepted = True
        submission.cosign_statement_of_truth_accepted = True
        submission.save()


class SubmissionReportUrlSerializer(serializers.Serializer):
    report_download_url = serializers.SerializerMethodField(
        label=_("download report url"),
        help_text=_(
            "The URL where the submission report can be downloaded. Note that this contain a timestamped token generated by the backend."
        ),
    )

    @extend_schema_field(OpenApiTypes.URI)
    def get_report_download_url(self, submission) -> str:
        return get_report_download_url(self.context["request"], submission.report)
