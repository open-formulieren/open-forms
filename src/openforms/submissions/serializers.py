"""
Non-API related serializers, typically used to validate data-structures in ``JSONField``
type model fields.
"""
from rest_framework import serializers

from openforms.authentication.registry import register


class CoSignDataSerializer(serializers.Serializer):
    plugin = serializers.ChoiceField(choices=())
    identifier = serializers.CharField()
    # TODO: validate fields shape depending on value of plugin (polymorphic serializer)
    fields = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        allow_null=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plugin"].choices = register.get_choices()
