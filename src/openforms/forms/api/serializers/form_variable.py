from collections import defaultdict

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openforms.submissions.form_logic import get_component

from ...constants import FormVariableSources
from ...models import FormVariable


class FormVariableListSerializer(serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("child", FormVariableSerializer())
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        variables_to_create = [
            FormVariable(**variable) for variable in self.validated_data
        ]
        return FormVariable.objects.bulk_create(variables_to_create)

    def validate(self, attrs):
        static_data_keys = [item.key for item in FormVariable.get_static_data()]

        existing_form_key_combinations = []
        errors = defaultdict(list)
        for index, item in enumerate(attrs):
            key_form_combination = (item["key"], item["form"].slug)
            if key_form_combination in existing_form_key_combinations:
                errors[f"{index}.key"].append(
                    serializers.ErrorDetail(
                        _("The variable key must be unique within a form"),
                        code="unique",
                    )
                )
                continue

            if item["key"] in static_data_keys:
                errors[f"{index}.key"].append(
                    serializers.ErrorDetail(
                        _(
                            "The variable key cannot be equal to any of the following values: {static_data}."
                        ).format(static_data=", ".join(static_data_keys)),
                        code="unique",
                    )
                )
                continue

            existing_form_key_combinations.append(key_form_combination)

        if errors:
            raise ValidationError(errors)

        return attrs


# TODO transform in polymorphic serializer to validate on different types of initial values?
class FormVariableSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FormVariable
        list_serializer_class = FormVariableListSerializer
        fields = (
            "form",
            "form_definition",
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

    def validate(self, attrs):
        if (form_definition := attrs.get("form_definition")) and attrs.get(
            "source"
        ) == FormVariableSources.component:
            component = get_component(form_definition.configuration, attrs["key"])
            if not component:
                raise ValidationError(
                    {
                        "key": _(
                            "Invalid component variable: "
                            "no component with corresponding key present in the form definition."
                        )
                    }
                )

        return attrs
