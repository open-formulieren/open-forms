from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class CommunicationChannels(TextChoices):
    email = "email", _("Email")
    phone_number = "phoneNumber", _("Phone number")


class OptionsSerializer(serializers.Serializer):
    address = serializers.CharField(
        label=_("Address"),
        help_text=_("An address value for the supported communication channels."),
    )
    verification_date = serializers.CharField(
        label=_("Verification date"),
        allow_null=True,
        help_text=_("The verification date of an address."),
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
