import logging
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from openforms.forms.api.serializers import FormDefinitionSerializer
from openforms.forms.models import FormStep

from ...forms.validators import validate_not_maintainance_mode
from ..constants import ProcessingResults, ProcessingStatuses
from ..form_logic import check_submission_logic, evaluate_form_logic
from ..models import Submission, SubmissionStep, TemporaryFileUpload
from .fields import NestedRelatedField

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

    optional = serializers.BooleanField(
        source="form_step.optional",
        read_only=True,
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
            "optional",
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
        # from SubmissionPayment model
        max_digits=8,
        decimal_places=2,
        source="form.product.price",
        help_text=_("Amount (to be) paid"),
        read_only=True,
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
    next_step = NestedRelatedField(
        view_name="api:submission-steps-detail",
        lookup_field="form_step__uuid",
        lookup_url_kwarg="step_uuid",
        source="get_next_step",
        read_only=True,
        allow_null=True,
        parent_lookup_kwargs={
            "submission_uuid": "submission__uuid",
        },
    )
    can_submit = serializers.BooleanField(
        label=_("can submit"),
        source="form.can_submit",
        help_text=_("Whether the user is allowed to submit this form."),
        required=False,
        read_only=True,
    )

    payment = NestedSubmissionPaymentDetailSerializer(
        label=_("payment information"),
        source="*",
        read_only=True,
    )

    class Meta:
        model = Submission
        fields = (
            "id",
            "url",
            "form",
            "steps",
            "next_step",
            "can_submit",
            "payment",
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
                    validate_not_maintainance_mode,
                ],
            },
        }

    def to_representation(self, instance):
        check_submission_logic(instance)
        return super().to_representation(instance)


class ContextAwareFormStepSerializer(serializers.ModelSerializer):
    configuration = serializers.SerializerMethodField()

    class Meta:
        model = FormStep
        fields = ("index", "configuration")
        extra_kwargs = {
            "index": {"source": "order"},
        }

    def get_configuration(self, instance) -> dict:
        # can't simply declare this because the JSON is stored as string in
        # the DB instead of actual JSON
        # FIXME: sort out the storing of configuration
        submission = self.root.instance.submission
        serializer = FormDefinitionSerializer(
            instance=instance.form_definition,
            context={**self.context, "submission": submission},
        )
        return serializer.data["configuration"]


class SubmissionStepSerializer(NestedHyperlinkedModelSerializer):
    form_step = ContextAwareFormStepSerializer(read_only=True)
    slug = serializers.SlugField(
        source="form_step.form_definition.slug",
        read_only=True,
    )

    optional = serializers.BooleanField(
        source="form_step.optional",
        read_only=True,
    )

    parent_lookup_kwargs = {
        "submission_uuid": "submission__uuid",
    }

    class Meta:
        model = SubmissionStep
        fields = (
            "id",
            "slug",
            "form_step",
            "data",
            "is_applicable",
            "completed",
            "optional",
            "can_submit",
        )

        extra_kwargs = {
            "id": {
                "read_only": True,
                "source": "uuid",
                "allow_null": True,
            },
        }

    def to_representation(self, instance):
        # invoke the configured form logic to dynamically update the Formio.js configuration
        evaluate_form_logic(instance.submission, instance, instance.submission.data)
        return super().to_representation(instance)


class FormDataSerializer(serializers.Serializer):
    data = serializers.JSONField(
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
        instance = super().update(instance, validated_data)
        transaction.on_commit(lambda: self.notify_suspension(instance, email))
        return instance

    def notify_suspension(self, instance: Submission, email: str):
        logger.info("TODO: properly implement sending e-mail with magic link")
        send_mail(
            _("Your form submission"),
            "Submission is suspended. Resume here: <link>",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )


class TemporaryFileUploadSerializer(serializers.Serializer):
    """
    https://help.form.io/integrations/filestorage/#url

    {
        url: 'http://link.to/file',
        name: 'The_Name_Of_The_File.doc',
        size: 1000
    }
    """

    file = serializers.FileField(write_only=True, required=True, use_url=False)

    url = serializers.SerializerMethodField(
        label=_("URL"), source="get_url", read_only=True
    )
    name = serializers.CharField(
        label=_("File name"), source="file_name", read_only=True
    )
    size = serializers.IntegerField(
        label=_("File size"), source="content.size", read_only=True
    )

    class Meta:
        model = TemporaryFileUpload
        fields = (
            "url",
            "name",
            "size",
        )

    def get_url(self, instance) -> str:
        request = self.context["request"]
        return reverse(
            "api:submissions:temporary-file",
            kwargs={"uuid": instance.uuid},
            request=request,
        )


class SubmissionStateLogicSerializer(serializers.Serializer):
    submission = SubmissionSerializer()
    step = SubmissionStepSerializer()


@dataclass
class SubmissionStateLogic:
    submission: Submission
    step: Optional[SubmissionStep] = None


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
        choices=ProcessingStatuses,
        default=ProcessingStatuses.in_progress,
        help_text=_(
            "The async task state, managed by the async task queue. Once the status is "
            "`done`, check the `result` field for the outcome."
        ),
    )
    result = serializers.ChoiceField(
        label=_("background processing result"),
        choices=ProcessingResults,
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

    # TODO: apply HTML sanitation here with bleach
    confirmation_page_content = serializers.CharField(
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
