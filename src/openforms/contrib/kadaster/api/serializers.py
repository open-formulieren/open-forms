from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class AddressSearcLatitudeLongitudeSerializer(serializers.Serializer):
    lat = serializers.FloatField(label=_("Latitude"))
    lng = serializers.FloatField(label=_("Longitude"))


class AddressSearcRijksDriehoekSerializer(serializers.Serializer):
    x = serializers.FloatField(label=_("X"))
    y = serializers.FloatField(label=_("Y"))


class AddressSearchResultSerializer(serializers.Serializer):
    label = serializers.CharField(label=_("The location name of the BAG location."))
    lat_lng = AddressSearcLatitudeLongitudeSerializer()
    rd = AddressSearcRijksDriehoekSerializer()
