from rest_framework import serializers

from ..models import Submission


class SubmissionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Submission
        fields = ('form', 'submitted_on', 'data')
        extra_kwargs = {
            "form": {
                "view_name": "api:form-detail",
                "lookup_field": "slug",
                "required": True,
                "allow_null": False,
            },
        }
