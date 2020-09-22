import json

from rest_framework import serializers

from openforms.core.models import Form, FormDefinition, FormSubmission


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
            'steps': steps
        }

    class Meta:
        model = Form
        fields = ('name', 'login_required', 'product', 'steps', )


class FormStepSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        return {
            'name': instance.name,
            'configuration': json.loads(instance.configuration)
        }

    class Meta:
        model = FormDefinition
        fields = ()


class FormSubmissionSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        return {
            'form': str(instance.form),
            'submitted_on': instance.submitted_on,
            'data': json.loads(instance.data)
        }

    class Meta:
        model = FormSubmission
        fields = ()


class FormDefinitionSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        return json.loads(instance.configuration)

    class Meta:
        model = FormDefinition
        fields = ()
