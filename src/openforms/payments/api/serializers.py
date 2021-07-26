from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.payments.constants import PaymentRequestType
from openforms.plugins.api.serializers import PluginBaseSerializer


class PaymentPluginSerializer(PluginBaseSerializer):
    # serializer for form builder
    pass


class PaymentOptionSerializer(serializers.Serializer):
    # serializer for form
    identifier = serializers.CharField(label=_("Identifier"), read_only=True)
    label = serializers.CharField(
        label=_("Button label"), help_text=_("Button label"), read_only=True
    )


class PaymentInfoSerializer(serializers.Serializer):
    # serializer for payment
    type = serializers.ChoiceField(
        label=_("Request type"), choices=PaymentRequestType.choices, read_only=True
    )
    url = serializers.URLField(label=_("URL"), read_only=True)
    data = serializers.DictField(
        label=_("Data"),
        child=serializers.CharField(label=_("Value"), read_only=True),
        read_only=True,
    )
