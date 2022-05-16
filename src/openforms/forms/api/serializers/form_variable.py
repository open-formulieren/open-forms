from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openforms.forms.models import FormVariable


class FormVariableListSerializer(serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        if "child" not in kwargs:
            kwargs = {**kwargs, **{"child": FormVariableSerializer()}}
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        variables_to_create = [
            FormVariable(**variable) for variable in self.validated_data
        ]
        return FormVariable.objects.bulk_create(variables_to_create)

    def validate(self, attrs):
        existing_form_key_combinations = []
        for item in attrs:
            key_form_combination = (item["key"], item["form"].slug)
            if key_form_combination in existing_form_key_combinations:
                raise ValidationError(
                    _("The form and key attributes must be unique together"),
                    code="invalid",
                )
            existing_form_key_combinations.append(key_form_combination)
        return attrs


# TODO transform in polymorphic serializer to validate on different types of initial values?
class FormVariableSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FormVariable
        list_serializer_class = FormVariableListSerializer
        fields = (
            "form",
            "name",
            "key",
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
