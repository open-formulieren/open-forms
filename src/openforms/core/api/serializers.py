from rest_framework import serializers

from openforms.core.models import FormDefinition


class FormSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        return {
            'name': instance.name,
            'url': instance.get_config_api_url(self.context['request'])
        }

    class Meta:
        model = FormDefinition
        fields = ('name', 'url',)
