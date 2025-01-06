from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class CatalogueSerializer(serializers.Serializer):
    """
    Serialize a catalogue option retrieved from the Catalogi API.

    The serializer includes the necessary fiels to display a human readable label,
    build the composite key that uniquely identifiers a catalogue (rsin + domain) and
    the API resource URL for subsequent filtering of resources inside the catalogue,
    like case and document types.

    If you need to store a reference to a catalogue, it's better to use another
    serializer (:class:`openforms.contrib.zgw.serializers.CatalogueSerializer`) instead,
    which only stores the composite key.
    """

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


class CaseTypeSerializer(serializers.Serializer):
    identification = serializers.CharField(
        label=_("identification"),
        help_text=_(
            "The unique identification within the catalogue for a given case type. "
            "Note that multiple versions of the same case type with the same "
            "identification exist."
        ),
    )
    description = serializers.CharField(
        label=_("description"),
        help_text=_(
            "The name/kind of case type based on which people can recognize/search "
            "a particular case type."
        ),
    )
    is_published = serializers.BooleanField(
        label=_("Is published"),
        help_text=_(
            "Unpublished case types may be returned when the feature flag "
            "'ZGW_APIS_INCLUDE_DRAFTS' is enabled."
        ),
    )


class DocumentTypeSerializer(serializers.Serializer):
    description = serializers.CharField(
        label=_("description"),
        help_text=_(
            "The description uniquely identifies a document type within a catalogue. "
            "Multiple versions of the same document type may exist, these have "
            "non-overlapping valid from/valid until dates."
        ),
    )
    is_published = serializers.BooleanField(
        label=_("Is published"),
        help_text=_(
            "Unpublished document types may be returned when the feature flag "
            "'ZGW_APIS_INCLUDE_DRAFTS' is enabled."
        ),
    )
    # DeprecationWarning - only relevant for Formio registration attributes
    url = serializers.URLField(label=_("url"))
    # DeprecationWarning - only relevant for Formio registration attributes
    catalogue_label = serializers.CharField(
        label=_("catalogue label"),
        help_text=_("A representation of the catalogue containing the document type."),
    )


class RoleTypeSerializer(serializers.Serializer):
    description = serializers.CharField(
        label=_("description"),
        help_text=_(
            "The description/label given to the role type in the Catalogi API. It "
            "identifies the role type within a case type."
        ),
    )
    description_generic = serializers.CharField(
        label=_("generic description"),
        help_text=_(
            "One of the pre-determined generic descriptions, such as 'behandelaar' "
            "or 'belanghebbende'."
        ),
    )


class CaseTypeProductSerializer(serializers.Serializer):
    url = serializers.CharField(
        label=_("url"),
        help_text=_("The url of a product bound to a case type. "),
    )
    description = serializers.CharField(
        label=_("description"),
        help_text=_("The description of a product bound to a case type. "),
        required=False,
        allow_blank=True,
    )
