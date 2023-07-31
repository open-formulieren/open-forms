from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class LatitudeLongitudeSerializer(serializers.Serializer):
    lat = serializers.FloatField(label=_("Latitude"))
    lng = serializers.FloatField(label=_("Longitude"))


class RijksDriehoekSerializer(serializers.Serializer):
    x = serializers.FloatField(label=_("X"))
    y = serializers.FloatField(label=_("Y"))


class AddressSearchResultSerializer(serializers.Serializer):
    label = serializers.CharField(label=_("Location name"))
    lat_lng = LatitudeLongitudeSerializer(
        label=_("Latitude/longitude"),
        help_text=_("Latitude and longitude in the WGS 84 coordinate system."),
    )
    rd = RijksDriehoekSerializer(
        label=_("Rijkdsdriehoek coordinates"),
        help_text=_(
            "X and Y coordinates in the "
            "[Rijkdsdriehoek](https://nl.wikipedia.org/wiki/Rijksdriehoeksco%C3%B6rdinaten)"
            " coordinate system."
        ),
        allow_null=True,
    )
