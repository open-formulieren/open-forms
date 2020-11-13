import json

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


class FormDefinitionSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        # TODO: json.loads on something that is a JSONField makes no sense,
        # track down the cause of this being a string instead of actual JSON
        parsed_config = json.loads(instance.configuration)
        parsed_config = handle_custom_types(
            parsed_config, request=self.context["request"]
        )
        return parsed_config

    class Meta:
        model = FormDefinition
        fields = ()


class FormStepSerializer(serializers.ModelSerializer):
    index = serializers.IntegerField(source="order")
    configuration = serializers.SerializerMethodField()

    parent_lookup_kwargs = {
        "form_uuid": "form__uuid",
    }

    class Meta:
        model = FormStep
        fields = ("index", "configuration")

    def get_configuration(self, instance):
        # can't simply declare this because the JSON is stored as string in
        # the DB instead of actual JSON
        serializer = FormDefinitionSerializer(
            instance=instance.form_definition,
            context=self.context,
        )
        return serializer.data
