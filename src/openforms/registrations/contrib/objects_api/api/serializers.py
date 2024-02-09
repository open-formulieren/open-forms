from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class ObjecttypeSerializer(serializers.Serializer):
    # Keys are defined in camel case as this is what we get from the Objecttype API
    url = serializers.URLField(
        label=_(
            "URL reference to this object. This is the unique identification and location of this object."
        ),
    )
    uuid = serializers.UUIDField(label=_("Unique identifier (UUID4)."))
    name = serializers.CharField(label=_("Name of the object type."))
    namePlural = serializers.CharField(label=_("Plural name of the object type."))
    dataClassification = serializers.CharField(
        label=_("Confidential level of the object type.")
    )


class ObjecttypeVersionSerializer(serializers.Serializer):
    version = serializers.IntegerField(
        label=_("Integer version of the Objecttype."),
    )
    status = serializers.CharField(label=_("Status of the object type version"))
