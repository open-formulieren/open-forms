import logging

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
            "available",
            "completed",
            "optional",
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

    class Meta:
        model = Submission
        fields = (
            "id",
            "url",
            "form",
            "steps",
            "next_step",
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


class SubmissionCompletionSerializer(serializers.Serializer):
    download_url = serializers.URLField(
        label=_("Report download url"),
        read_only=True,
        help_text=_(
            "The URL where the PDF report with submission data can be downloaded from."
        ),
    )
    report_status_url = serializers.URLField(
        label=_("Report status url"),
        read_only=True,
        help_text=_(
            "The endpoint where the PDF report generation status can be checked."
        ),
    )
    # TODO: apply HTML sanitation here with bleach
    confirmation_page_content = serializers.CharField(
        label=_("Confirmation page content"),
        read_only=True,
        help_text=_("Body text of the confirmation page. May contain HTML!"),
    )


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
        )

        extra_kwargs = {
            "id": {
                "read_only": True,
                "source": "uuid",
                "allow_null": True,
            },
        }


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


class ReportStatusSerializer(serializers.Serializer):
    # from https://docs.celeryproject.org/en/stable/reference/celery.result.html#celery.result.AsyncResult.status
    status = serializers.ChoiceField(
        label=_("Status"),
        choices=(
            ("PENDING", _("The task is waiting for execution.")),
            ("STARTED", _("The task has been started.")),
            ("RETRY", _("The task is to be retried, possibly because of failure.")),
            ("FAILURE", _("The task has failed.")),
            ("SUCCESS", _("The task executed successfully.")),
        ),
        allow_null=True,
        help_text=_(
            "Status of the background task responsible for generating the submission data PDF."
        ),
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
        label=_("Url"), source="get_url", read_only=True
    )
    name = serializers.URLField(
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

    def get_url(self, instance):
        request = self.context["request"]
        return reverse(
            "api:submissions:temporary-file",
            kwargs={"uuid": instance.uuid},
            request=request,
        )
