import json

from rest_framework import serializers

from openforms.core.models import Form, FormDefinition, FormStep
from openforms.contrib.handlers import handle_custom_types


class FormSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        request = self.context["request"]
        if not request.session.get(instance.slug):
            request.session[instance.slug] = {"current_step": instance.first_step}

        steps = instance.get_api_form_steps(self.context["request"])

        return {
            'name': instance.name,
            'login_required': instance.login_required,
            'product': str(instance.product),
            'user_current_step': steps[request.session[instance.slug]['current_step']],
            'steps': steps,
            'slug': instance.slug,
            'url': instance.get_api_url(),
        }

    class Meta:
        model = Form
        fields = (
            "name",
            "login_required",
            "product",
            "steps",
        )


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
