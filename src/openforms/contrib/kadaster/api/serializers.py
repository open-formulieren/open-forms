from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class GetStreetNameAndCityViewInputSerializer(serializers.Serializer):
    postcode = serializers.CharField(
        label=_("postal code"), help_text=_("Postal code to use in search")
    )
    house_number = serializers.CharField(
        label=_("house number"), help_text=_("House number to use in search")
    )


class GetStreetNameAndCityViewResultSerializer(serializers.Serializer):
    street_name = serializers.CharField(
        label=_("street name"), help_text=_("Found street name")
    )
    city = serializers.CharField(label=_("city"), help_text=_("Found city"))
    secret_street_city = serializers.CharField(
        label=_("city and street name secret"),
        help_text=_("Secret for the combination of city and street name"),
        required=False,
        allow_blank=True,
    )


class LatitudeLongitudeSerializer(serializers.Serializer):
    lat = serializers.FloatField(label=_("Latitude"))
    lng = serializers.FloatField(label=_("Longitude"))


class RijksDriehoekSerializer(serializers.Serializer):
    x = serializers.FloatField(label=_("X"))
    y = serializers.FloatField(label=_("Y"))


class AddressSearchResultSerializer(serializers.Serializer):
    label = serializers.CharField(label=_("Location name"))  # type: ignore
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


class LatLngSearchInputSerializer(serializers.Serializer):
    lat = serializers.FloatField(
        label=_("Latitude"),
        help_text=_("Latitude, in decimal degrees."),
        required=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    lng = serializers.FloatField(
        label=_("Longitude"),
        help_text=_("Longitude, in decimal degrees."),
        required=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )


class LatLngSearchResultSerializer(serializers.Serializer):
    label = serializers.CharField(label=_("Closest address"))  # type: ignore
