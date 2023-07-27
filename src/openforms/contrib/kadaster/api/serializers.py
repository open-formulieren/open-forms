from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class MapSearchLatitudeLongitudeSerializer(serializers.Serializer):
    lat = serializers.FloatField(label=_("Latitude"))
    lng = serializers.FloatField(label=_("Longitude"))


class MapSearchRijksDriehoekSerializer(serializers.Serializer):
    x = serializers.FloatField(label=_("X"))
    y = serializers.FloatField(label=_("Y"))


class MapSearchSerializer(serializers.Serializer):
    label = serializers.CharField(label=_("The location name of the BAG location."))
    latLng = MapSearchLatitudeLongitudeSerializer()
    rd = MapSearchRijksDriehoekSerializer()
