import json

from rest_framework import serializers

from openforms.core.models import Form, FormDefinition, FormStep


class FormSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        request = self.context['request']
        if not request.session.get(instance.slug):
            request.session[instance.slug] = {
                'current_step': instance.first_step
            }

        steps = instance.get_api_form_steps(self.context['request'])

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
        fields = ('name', 'login_required', 'product', 'steps', )


class FormStepSerializer(serializers.ModelSerializer):
    index = serializers.IntegerField(source="order")
    configuration = serializers.SerializerMethodField()

    class Meta:
        model = FormStep
        fields = ("index", "configuration",)

    def get_configuration(self, obj):
        return json.loads(obj.form_definition.configuration)


class FormDefinitionSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        return json.loads(instance.configuration)

    class Meta:
        model = FormDefinition
        fields = ()
