"""
Non-API related serializers, typically used to validate data-structures in ``JSONField``
type model fields.
"""

from rest_framework import serializers

# import from `constants` to avoid circ. import:
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import register


class CoSignDataSerializer(serializers.Serializer):
    plugin = serializers.ChoiceField(choices=())
    identifier = serializers.CharField()
    representation = serializers.CharField(required=False, allow_blank=True, default="")
    co_sign_auth_attribute = serializers.ChoiceField(choices=AuthAttribute.choices)
    # TODO: validate fields shape depending on value of plugin (polymorphic serializer)
    fields = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        allow_null=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plugin"].choices = register.get_choices()
