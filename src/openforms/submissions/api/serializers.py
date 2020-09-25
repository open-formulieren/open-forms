from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from ..models import Submission, SubmissionStep
from openforms.core.models import FormStep
from openforms.core.backends import registry


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
        fields = ('uuid', 'url', 'form', 'steps', 'created_on', 'completed_on')
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
                "lookup_field": "slug",
            },
        }

    def save(self, *args, **kwargs):
        bsn = self.context['request'].session.get('bsn')
        if bsn:
            kwargs["bsn"] = bsn
        return super().save(*args, **kwargs)


class SubmissionStepSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        "submission_uuid": "submission__uuid",
    }

    form_step = NestedHyperlinkedRelatedField(
        # many=True,
        # read_only=True,   # Or add a queryset
        queryset=FormStep.objects,
        view_name='api:form-steps-detail',
        lookup_field="order",
        parent_lookup_kwargs={'form_slug': 'form__slug'}
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

    def save(self, *args, **kwargs):
        # TODO: I forgot how to nicely do this.
        kwargs.update({
            "submission": Submission.objects.get(
                uuid=self.context['request'].parser_context['view'].kwargs['submission_uuid']
            )
        })
        submission_step = super().save(*args, **kwargs)

        # run form backend
        # TODO should run only on the final submit of the form
        # TODO should be done after merging all data in submission model and marking final submission steps
        backend_func = registry.get(submission_step.submission.form.backend)
        if backend_func:
            result = backend_func(submission_step)
            submission = submission_step.submission
            submission.backend_result = result
            submission.save()

        return submission_step
