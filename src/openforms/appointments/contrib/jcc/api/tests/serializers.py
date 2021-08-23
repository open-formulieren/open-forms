from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    code = serializers.CharField(label=_("code"), help_text=_("Product code"))
    identifier = serializers.CharField(
        label=_("identifier"), help_text=_("Product identifier")
    )
    name = serializers.CharField(label=_("name"), help_text=_("Product name"))


class LocationSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        label=_("identifier"), help_text=_("Location identifier")
    )
    name = serializers.CharField(label=_("name"), help_text=_("Product name"))


class LocationInputSerializer(serializers.Serializer):
    product_id = serializers.CharField(
        label=_("product id"), help_text=_("Id of the product to get locations for")
    )


class DateInputSerializer(serializers.Serializer):
    product_id = serializers.CharField(
        label=_("product id"), help_text=_("Id of the product to get dates for")
    )
    location_id = serializers.CharField(
        label=_("location id"), help_text=_("Id of the location to get dates for")
    )


class TimeInputSerializer(serializers.Serializer):
    product_id = serializers.CharField(
        label=_("product id"), help_text=_("Id of the product to get times for")
    )
    location_id = serializers.CharField(
        label=_("location id"), help_text=_("Id of the location to get times for")
    )
    date = serializers.DateField(label=_("date"), help_text=_("Date to get times for"))
