from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class CommunicationChannels(TextChoices):
    email = "email", _("Email")
    phone_number = "phoneNumber", _("Phone number")


class OptionsSerializer(serializers.Serializer):
    address = serializers.CharField(
        label=_("Address"),
        read_only=True,
        help_text=_("An address value for the supported communication channels."),
    )
    is_verified = serializers.BooleanField(
        label=_("Is address verified"),
        read_only=True,
        help_text=_("Whether the address is verified or not."),
    )


class CommunicationPreferencesSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        label=_("Type"),
        choices=CommunicationChannels.choices,
        help_text=_("Communication channel type"),
    )
    options = OptionsSerializer(many=True)
    preferred = serializers.CharField(
        label=_("Preferred"),
        allow_null=True,
        help_text=_("Preferred address option for this channel"),
    )
