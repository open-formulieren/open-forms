from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class GetStreetNameAndCityViewInputSerializer(serializers.Serializer):
    postcode = serializers.CharField(
        label=_("postcode"), help_text=_("Postcode to use in search")
    )
    huisnummer = serializers.CharField(
        label=_("house number"), help_text=_("House number to use in search")
    )


class GetStreetNameAndCityViewResultSerializer(serializers.Serializer):
    street_name = serializers.CharField(
        source="korteNaam", label=_("street name"), help_text=_("Found street name")
    )
    city = serializers.CharField(
        source="woonplaatsNaam", label=_("city"), help_text=_("Found city")
    )
