from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class CatalogueSerializer(serializers.Serializer):
    domain = serializers.CharField(label=_("domain"))
    rsin = serializers.CharField(label=_("rsin"))
    label = serializers.CharField(  # type: ignore
        label=_("label"), help_text=_("The display label of the catalogue")
    )
    url = serializers.URLField(
        label=_("url"),
        help_text=_(
            "The API resource URL of the catalogue. You can use this for subsequent "
            "filtering operations.",
        ),
    )


# TODO: OF 3.0 -> use English instead of Dutch.
class InformatieObjectTypeSerializer(serializers.Serializer):
    url = serializers.URLField(label=_("url"))
    omschrijving = serializers.CharField(
        label=_("description"),
        help_text=_(
            "The description uniquely identifies a document type within a catalogue. "
            "Multiple versions of the same document type may exist, these have "
            "non-overlapping valid from/valid until dates."
        ),
    )
    catalogus_label = serializers.CharField(
        label=_("catalogue label"),
        help_text=_("A representation of the catalogue containing the document type."),
    )
