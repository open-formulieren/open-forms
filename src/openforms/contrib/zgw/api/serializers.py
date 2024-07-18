from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class CatalogusSerializer(serializers.Serializer):
    domein = serializers.CharField(label=_("domein"))
    rsin = serializers.CharField(label=_("rsin"))
    label = serializers.CharField(
        label=_("label"), help_text=_("The display label of the catalogus")
    )


class InformatieObjectTypeSerializer(serializers.Serializer):
    catalogus_domein = serializers.CharField(label=_("catalogus domein"))
    catalogus_rsin = serializers.CharField(label=_("catalogus rsin"))
    catalogus_label = serializers.CharField(
        label=_("catalogus label"), help_text=_("The display label of the catalogus")
    )
    url = serializers.URLField(label=_("url"))
    omschrijving = serializers.CharField(label=_("omschrijving"))
