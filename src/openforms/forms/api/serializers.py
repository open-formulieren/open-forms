from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.products.api.serializers import ProductSerializer

from ..custom_field_types import handle_custom_types
from ..models import Form, FormDefinition, FormStep


class MinimalFormStepSerializer(serializers.ModelSerializer):
    form_definition = serializers.SlugRelatedField(read_only=True, slug_field="name")
    index = serializers.IntegerField(source="order")
    url = NestedHyperlinkedRelatedField(
        queryset=FormStep.objects,
        source="*",
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid": "form__uuid"},
    )

    class Meta:
        model = FormStep
        fields = (
            "uuid",
            "form_definition",
            "index",
            "url",
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            }
        }


class FormSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    steps = MinimalFormStepSerializer(many=True, read_only=True, source="formstep_set")

    class Meta:
        model = Form
        fields = ("uuid", "name", "login_required", "product", "slug", "url", "steps")
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "url": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
            },
        }


class FormDefinitionSerializer(serializers.HyperlinkedModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance=instance)

        _handle_custom_types = self.context.get("handle_custom_types", True)
        if _handle_custom_types:
            representation["configuration"] = handle_custom_types(
                representation["configuration"],
                request=self.context["request"],
                submission=self.context["submission"],
            )
        return representation

    class Meta:
        model = FormDefinition
        fields = (
            "url",
            "uuid",
            "name",
            "slug",
            "configuration",
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            }
        }


class FormStepSerializer(serializers.ModelSerializer):
    index = serializers.IntegerField(source="order")
    configuration = serializers.JSONField(source="form_definition.configuration")

    parent_lookup_kwargs = {
        "form_uuid": "form__uuid",
    }

    def create(self, validated_data):
        validated_data["form"] = self.context["form"]
        config = validated_data["form_definition"]["configuration"]

        # FIXME the identity of the related FormDefinition and Form can't
        # be determined from the request body, so the FormStep shape in the API
        # should probably change?
        validated_data["form_definition"] = FormDefinition.objects.filter(
            configuration=config
        ).last()
        return super().create(validated_data)

    class Meta:
        model = FormStep
        fields = ("index", "configuration")
