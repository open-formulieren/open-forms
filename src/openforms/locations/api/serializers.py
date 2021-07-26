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
