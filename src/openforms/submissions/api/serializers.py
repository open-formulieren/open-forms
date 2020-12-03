from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from openforms.core.api.serializers import FormDefinitionSerializer
from openforms.core.models import FormStep

from ..models import Submission, SubmissionStep
from .fields import NestedSubmissionRelatedField


class NestedSubmissionStepSerializer(NestedHyperlinkedModelSerializer):
    id = serializers.UUIDField(source="form_step.uuid")
    name = serializers.CharField(source="form_step.form_definition.name")

    url = NestedSubmissionRelatedField(
        view_name="api:submission-steps-detail",
        source="*",
        lookup_field="form_step__uuid",
        lookup_url_kwarg="step_uuid",
        instance_lookup_kwargs={
            "submission_uuid": "submission__uuid",
        },
    )

    form_step = NestedSubmissionRelatedField(
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        lookup_url_kwarg="uuid",
        instance_lookup_kwargs={
            "form_uuid": "form__uuid",
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
    next_step = NestedSubmissionRelatedField(
        view_name="api:submission-steps-detail",
        lookup_field="uuid",
        lookup_url_kwarg="step_uuid",
        source="get_next_step",
        read_only=True,
        allow_null=True,
        instance_lookup_kwargs={
            "submission_uuid": "uuid",
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
            },
        }


class ContextAwareFormStepSerializer(serializers.ModelSerializer):
    configuration = serializers.SerializerMethodField()

    class Meta:
        model = FormStep
        fields = ("index", "configuration")
        extra_kwargs = {
            "index": {"source": "order"},
        }

    def get_configuration(self, instance):
        # can't simply declare this because the JSON is stored as string in
        # the DB instead of actual JSON
        # FIXME: sort out the storing of configuration
        submission = self.root.instance.submission
        serializer = FormDefinitionSerializer(
            instance=instance.form_definition,
            context={**self.context, "submission": submission},
        )
        return serializer.data


class SubmissionStepSerializer(NestedHyperlinkedModelSerializer):
    form_step = ContextAwareFormStepSerializer(read_only=True)

    parent_lookup_kwargs = {
        "submission_uuid": "submission__uuid",
    }

    class Meta:
        model = SubmissionStep
        fields = (
            "id",
            "form_step",
            "data",
        )

        extra_kwargs = {
            "id": {
                "read_only": True,
                "source": "uuid",
            },
        }
