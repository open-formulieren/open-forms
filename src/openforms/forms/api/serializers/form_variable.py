from rest_framework import serializers

from openforms.forms.models import FormVariable


class FormVariableListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        return super().create(validated_data)


# TODO transform in polymorphic serializer to validate on different types of initial values?
class FormVariableSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FormVariable
        list_serializer_class = FormVariableListSerializer
        fields = (
            "form",
            "name",
            "slug",
            "source",
            "prefill_plugin",
            "prefill_attribute",
            "data_type",
            "data_format",
            "is_sensitive_data",
            "initial_value",
        )
        extra_kwargs = {
            "form": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
            "form_definition": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid",
            },
        }
