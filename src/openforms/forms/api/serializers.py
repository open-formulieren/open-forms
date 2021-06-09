from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.prefill import apply_prefill
from openforms.products.api.serializers import ProductSerializer

from ..custom_field_types import handle_custom_types
from ..models import Form, FormDefinition, FormStep


class MinimalFormStepSerializer(serializers.ModelSerializer):
    form_definition = serializers.SlugRelatedField(read_only=True, slug_field="name")
    index = serializers.IntegerField(source="order")
    slug = serializers.SlugField(source="form_definition.slug")
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
                "lookup_url_kwarg": "uuid_or_slug",
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
            representation["configuration"] = apply_prefill(
                representation["configuration"],
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


class FormStepSerializer(serializers.HyperlinkedModelSerializer):
    index = serializers.IntegerField(source="order", read_only=True)
    configuration = serializers.JSONField(
        source="form_definition.configuration", read_only=True
    )

    parent_lookup_kwargs = {
        "form_uuid_or_slug": "form__uuid",
    }

    class Meta:
        model = FormStep
        fields = (
            "index",
            # "slug",
            "configuration",
            "form_definition",
        )

        extra_kwargs = {
            "form_definition": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            },
        }

    def create(self, validated_data):
        validated_data["form"] = self.context["form"]
        return super().create(validated_data)


class FormImportSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text=_("The file that contains the form, form definitions and form steps.")
    )
