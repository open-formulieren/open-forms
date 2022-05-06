from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from ...models import FormStep
from .button_text import ButtonTextSerializer


class FormStepLiteralsSerializer(serializers.Serializer):
    previous_text = ButtonTextSerializer(raw_field="previous_text", required=False)
    save_text = ButtonTextSerializer(raw_field="save_text", required=False)
    next_text = ButtonTextSerializer(raw_field="next_text", required=False)


class MinimalFormStepSerializer(serializers.ModelSerializer):
    form_definition = serializers.SlugRelatedField(read_only=True, slug_field="name")
    index = serializers.IntegerField(source="order")
    slug = serializers.SlugField(source="form_definition.slug")
    literals = FormStepLiteralsSerializer(source="*", required=False)
    url = NestedHyperlinkedRelatedField(
        queryset=FormStep.objects,
        source="*",
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
    )

    class Meta:
        model = FormStep
        fields = (
            "uuid",
            "slug",
            "form_definition",
            "index",
            "literals",
            "url",
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            }
        }


class FormStepSerializer(serializers.HyperlinkedModelSerializer):
    index = serializers.IntegerField(source="order")
    configuration = serializers.JSONField(
        source="form_definition.configuration", read_only=True
    )
    login_required = serializers.BooleanField(
        source="form_definition.login_required", read_only=True
    )
    is_reusable = serializers.BooleanField(
        source="form_definition.is_reusable", read_only=True
    )
    name = serializers.CharField(source="form_definition.name", read_only=True)
    internal_name = serializers.CharField(
        source="form_definition.internal_name", read_only=True
    )
    slug = serializers.CharField(source="form_definition.slug", read_only=True)
    literals = FormStepLiteralsSerializer(source="*", required=False)
    url = NestedHyperlinkedRelatedField(
        source="*",
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
        read_only=True,
    )

    parent_lookup_kwargs = {
        "form_uuid_or_slug": "form__uuid",
    }

    class Meta:
        model = FormStep
        fields = (
            "uuid",
            "index",
            "slug",
            "configuration",
            "form_definition",
            "name",
            "internal_name",
            "url",
            "login_required",
            "is_reusable",
            "literals",
        )

        extra_kwargs = {
            "form_definition": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            },
            "uuid": {
                "read_only": True,
            },
        }

    def create(self, validated_data):
        validated_data["form"] = self.context["form"]
        return super().create(validated_data)
