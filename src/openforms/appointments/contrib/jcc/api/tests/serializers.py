from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    code = serializers.CharField(label=_("code"), help_text=_("Product code"))
    identifier = serializers.CharField(
        label=_("identifier"), help_text=_("Product identifier")
    )
    name = serializers.CharField(label=_("name"), help_text=_("Product name"))
