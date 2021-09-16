from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    code = serializers.CharField(label=_("code"), help_text=_("Product code"))
    identifier = serializers.CharField(
        label=_("identifier"), help_text=_("ID of the product")
    )
    name = serializers.CharField(label=_("name"), help_text=_("Product name"))


class LocationSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        label=_("identifier"), help_text=_("ID of the location")
    )
    name = serializers.CharField(label=_("name"), help_text=_("Location name"))


class LocationInputSerializer(serializers.Serializer):
    product_id = serializers.CharField(
        label=_("product ID"), help_text=_("ID of the product to get locations for")
    )


class DateInputSerializer(serializers.Serializer):
    product_id = serializers.CharField(
        label=_("product ID"), help_text=_("ID of the product to get dates for")
    )
    location_id = serializers.CharField(
        label=_("location ID"), help_text=_("ID of the location to get dates for")
    )


class DateSerializer(serializers.Serializer):
    date = serializers.DateField(label=_("date"))


class TimeInputSerializer(serializers.Serializer):
    product_id = serializers.CharField(
        label=_("product ID"), help_text=_("ID of the product to get times for")
    )
    location_id = serializers.CharField(
        label=_("location ID"), help_text=_("ID of the location to get times for")
    )
    date = serializers.DateField(label=_("date"), help_text=_("Date to get times for"))


class TimeSerializer(serializers.Serializer):
    time = serializers.DateTimeField(label=_("time"))


class CancelAppointmentInputSerializer(serializers.Serializer):
    email = serializers.EmailField(
        label=_("email"), help_text=_("Email given when making the appointment")
    )
