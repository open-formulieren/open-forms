from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from openforms.core.models import FormStep

from ..models import Submission, SubmissionStep


class SubmissionSerializer(serializers.HyperlinkedModelSerializer):
    steps = NestedHyperlinkedRelatedField(
        source="submissionstep_set",
        many=True,
        read_only=True,
        view_name='api:submission-steps-detail',
        lookup_field="uuid",
        parent_lookup_kwargs={'submission_uuid': 'submission__uuid'}
    )

    class Meta:
        model = Submission
        fields = ('uuid', 'url', 'form', 'current_step', 'steps', 'created_on', 'completed_on')
        extra_kwargs = {
            "uuid": {
                "read_only": True,
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


class SubmissionStepSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        "submission_uuid": "submission__uuid",
    }

    form_step = NestedHyperlinkedRelatedField(
        # many=True,
        # read_only=True,   # Or add a queryset
        queryset=FormStep.objects,
        view_name='api:form-steps-detail',
        lookup_field='uuid',
        parent_lookup_kwargs={'form_uuid': 'form__uuid'}
    )

    class Meta:
        model = SubmissionStep
        fields = ('uuid', 'url', 'submission', 'form_step', 'data', 'created_on')
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "url": {
                "view_name": "api:submission-steps-detail",
                "lookup_field": "uuid",
                "parent_lookup_kwargs": {
                    'submission_uuid': 'submission__uuid'
                }
            },
            "submission": {
                "view_name": "api:submission-detail",
                "lookup_field": "uuid",
                "read_only": True,
            },
        }
