from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.products.api.serializers import ProductSerializer

from ..custom_field_types import handle_custom_types
from ..models import Form, FormDefinition, FormStep
from .validators import FormDefinitionValidator, FormValidator


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
    index = serializers.IntegerField(source="order", read_only=True)
    configuration = serializers.JSONField(
        source="form_definition.configuration", read_only=True
    )
    form_definition = serializers.UUIDField(write_only=True)

    parent_lookup_kwargs = {
        "form_uuid": "form__uuid",
    }

    validators = [
        FormValidator(),
        FormDefinitionValidator(),
    ]

    class Meta:
        model = FormStep
        fields = ("index", "configuration", "form_definition")

    def update(self, instance, validated_data):
        instance.form_definition = FormDefinition.objects.get(
            uuid=validated_data["form_definition"]
        )
        instance.save()

        return instance

    def create(self, validated_data):

        form = Form.objects.get(uuid=self.context["view"].kwargs["form_uuid"])
        form_definition = FormDefinition.objects.get(
            uuid=validated_data["form_definition"]
        )

        return FormStep.objects.create(form=form, form_definition=form_definition)
