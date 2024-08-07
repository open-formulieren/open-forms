from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class CatalogueSerializer(serializers.Serializer):
    domain = serializers.CharField(label=_("domain"))
    rsin = serializers.CharField(label=_("rsin"))
    label = serializers.CharField(  # type: ignore
        label=_("label"), help_text=_("The display label of the catalogue")
    )


class InformatieObjectTypeSerializer(serializers.Serializer):
    catalogus_domein = serializers.CharField(label=_("catalogus domein"))
    catalogus_rsin = serializers.CharField(label=_("catalogus rsin"))
    catalogus_label = serializers.CharField(
        label=_("catalogus label"), help_text=_("The display label of the catalogus")
    )
    url = serializers.URLField(label=_("url"))
    omschrijving = serializers.CharField(label=_("omschrijving"))
