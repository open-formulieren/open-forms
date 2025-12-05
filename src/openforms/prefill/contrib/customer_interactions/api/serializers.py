from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class CommunicationChannels(TextChoices):
    email = "email", _("Email")
    phone_number = "phoneNumber", _("Phone number")


class CommunicationPreferencesSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        label=_("Type"),
        choices=CommunicationChannels.choices,
        help_text=_("Communication channel type"),
    )
    options = serializers.ListField(
        child=serializers.CharField(),
        label=_("Options"),
        help_text=_("List of available address options for this channel"),
    )
    preferred = serializers.CharField(
        label=_("Preferred"),
        allow_null=True,
        help_text=_("Preferred address option for this channel"),
    )
