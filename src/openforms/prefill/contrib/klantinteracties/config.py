from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin


class KlantInteractiesOptionsSerializer(
    JsonSchemaSerializerMixin, serializers.Serializer
):
    email = serializers.BooleanField(
        label=_("Email"),
        help_text=_("Whether emails are included in the prefill values"),
    )
    phone_number = serializers.BooleanField(
        label=_("Phone number"),
        help_text=_("Whether phone numbers are included in the prefill values"),
    )

    def validate(self, attrs):
        validated_attrs = super().validate(attrs)

        if not validated_attrs["email"] and not validated_attrs["phone_number"]:
            raise serializers.ValidationError(
                _("You must enable at least one digital address type.")
            )

        return validated_attrs
