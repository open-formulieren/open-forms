from django.db import transaction
from django.utils.functional import cached_property
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from openforms.formio.service import build_serializer
from openforms.forms.models import Form
from openforms.submissions.api.fields import PrivacyPolicyAcceptedField
from openforms.submissions.models import Submission

from ..base import BasePlugin, Product
from ..models import Appointment, AppointmentProduct, AppointmentsConfig
from ..utils import get_plugin
from .fields import LocationIDField, ProductIDField


class AppointmentOptionsSerializer(serializers.Serializer):
    # TODO: validate that appointments cannot be enabled if there's no plugin configured
    is_appointment = serializers.BooleanField(
        label=_("Is appointment form"),
        help_text=_(
            "Boolean indicating if the form is an appointment form, using the new flow."
        ),
    )
    supports_multiple_products = serializers.SerializerMethodField(
        label=_("Multiple products supported?"),
        help_text=_(
            "If not supported, only one product/service can be booked at once and the "
            "UI may not allow the user to select multiple products."
        ),
    )

    @cached_property
    def _appointment_plugin(self) -> BasePlugin | None:
        try:
            return get_plugin()
        except ValueError:  # appointments plugin is not configured
            return None

    def get_supports_multiple_products(self, obj: Form) -> bool | None:
        # not an appointment -> don't bother looking up plugin configuration
        if not obj.is_appointment:
            return None
        plugin = self._appointment_plugin
        return plugin.supports_multiple_products if plugin else None


class ProductSerializer(serializers.Serializer):
    code = serializers.CharField(label=_("code"), help_text=_("Product code"))
    identifier = serializers.CharField(
        label=_("identifier"), help_text=_("ID of the product")
    )
    name = serializers.CharField(label=_("name"), help_text=_("Product name"))
    description = serializers.CharField(
        label=_("description"),
        help_text=_("Product extra description"),
        allow_blank=True,
    )

    class Meta:
        ref_name = "AppointmentProduct"


class ProductInputSerializer(serializers.Serializer):
    product_id = serializers.ListField(
        child=ProductIDField(help_text=_("ID of a selected product.")),
        label=_("Product IDs"),
        help_text=_(
            "One or more product IDs already selected, which may limit the collection "
            "of additional products to select."
        ),
        required=False,
    )


class LocationSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        label=_("identifier"), help_text=_("ID of the location")
    )
    name = serializers.CharField(label=_("name"), help_text=_("Location name"))
    city = serializers.CharField(
        label=_("city"),
        allow_blank=True,
        help_text=_("City"),
    )
    address = serializers.CharField(
        label=_("address"),
        allow_blank=True,
        help_text=_("Address"),
    )
    postalcode = serializers.CharField(
        label=_("postal code"),
        allow_blank=True,
        help_text=_("Postal code"),
    )


class LocationInputSerializer(serializers.Serializer):
    product_id = serializers.ListField(
        child=ProductIDField(help_text=_("ID of the product to get locations for")),
        label=_("Product IDs"),
        help_text=_("One or more product IDs to get available locations for."),
        min_length=1,
    )


class DateInputSerializer(serializers.Serializer):
    product_id = serializers.ListField(
        child=ProductIDField(help_text=_("ID of the product to get dates for")),
        label=_("Product IDs"),
        help_text=_("One or more product IDs to get available dates for."),
        min_length=1,
    )
    location_id = LocationIDField(help_text=_("ID of the location to get dates for"))


class DateSerializer(serializers.Serializer):
    date = serializers.DateField(label=_("date"))


class TimeInputSerializer(serializers.Serializer):
    product_id = serializers.ListField(
        child=ProductIDField(help_text=_("ID of the product to get times for")),
        label=_("Product IDs"),
        help_text=_("One or more product IDs to get available times for."),
        min_length=1,
    )
    location_id = LocationIDField(help_text=_("ID of the location to get times for"))
    date = serializers.DateField(label=_("date"), help_text=_("Date to get times for"))


class TimeSerializer(serializers.Serializer):
    time = serializers.DateTimeField(label=_("time"))


class CancelAppointmentInputSerializer(serializers.Serializer):
    email = serializers.EmailField(
        label=_("email"), help_text=_("Email given when making the appointment")
    )


class CustomerFieldsInputSerializer(serializers.Serializer):
    product_id = serializers.ListField(
        child=ProductIDField(
            help_text=_("ID of the product to get required fields for")
        ),
        label=_("Product IDs"),
        help_text=_("One or more product IDs to get required fields for."),
        min_length=1,
    )


class AppointmentProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentProduct
        fields = ("product_id", "amount")
        ref_name = "_AppointmentProduct"


class PermissionSerializer(serializers.Serializer):
    submission = serializers.HyperlinkedRelatedField(
        required=True,
        queryset=Submission.objects.all(),
        view_name="api:submission-detail",
        lookup_field="uuid",
    )


class AppointmentSerializer(serializers.HyperlinkedModelSerializer):
    products = AppointmentProductSerializer(
        many=True,
        label=_("Products"),
    )
    date = serializers.DateField(label=_("date"))
    privacy_policy_accepted = PrivacyPolicyAcceptedField(write_only=True)
    status_url = serializers.SerializerMethodField(
        label=_("status check endpoint"),
        read_only=True,
        help_text=_(
            "The API endpoint where the background processing status can be checked. "
            "After calling the completion endpoint, this status URL should be polled "
            "to report the processing status back to the end-user. Note that the "
            "endpoint contains a token which invalidates on state changes and after "
            "one day."
        ),
    )
    contact_details = serializers.DictField(
        label=_("contact details"),
        help_text=_("Additional contact detail field values."),
        required=True,
        allow_null=False,
    )

    _status_url: str  # set by the view

    class Meta:
        model = Appointment
        fields = (
            "submission",
            "products",
            "location",
            "date",
            "datetime",
            "contact_details",
            "privacy_policy_accepted",
            "status_url",
        )
        extra_kwargs = {
            "submission": {
                "view_name": "api:submission-detail",
                "lookup_field": "uuid",
            },
        }

    def validate(self, attrs: dict) -> dict:
        date = attrs.pop("date")
        expected_date = localdate(attrs["datetime"])
        if date != expected_date:
            raise serializers.ValidationError(
                {
                    "date": _(
                        "The provided date does not match the full appointment datetime."
                    )
                }
            )

        config = AppointmentsConfig.get_solo()
        plugin = get_plugin()
        # normalize to data class instances to call plugin methods
        products = [
            Product(identifier=product["product_id"], name="")
            for product in attrs["products"]
        ]

        # validate the amount of products
        if not plugin.supports_multiple_products and len(products) > 1:
            raise serializers.ValidationError(
                {
                    "products": _(
                        "Appointments for multiple products are not supported."
                    ),
                }
            )

        # now run 'expensive' validations requiring network IO

        # 1. get the available products from the plugin and check them
        available_products = plugin.get_available_products(
            location_id=config.limit_to_location
        )
        available_product_ids = set(p.identifier for p in available_products)

        product_errors = []
        for product in products:
            valid_product = product.identifier in available_product_ids
            product_errors.append(
                {}
                if valid_product
                else {"product_id": _("Product is unknown in the appointment backend.")}
            )
        if any(err != {} for err in product_errors):
            raise serializers.ValidationError({"products": product_errors})

        # 2. Products are valid, check the location now.
        location_error = serializers.ValidationError(
            {"location": _("The requested location is not available.")}
        )
        if (location_id := config.limit_to_location) and attrs[
            "location"
        ] != location_id:
            raise location_error
        locations = {
            location.identifier: location for location in plugin.get_locations(products)
        }
        if not (_location := locations.get(attrs["location"])):
            raise location_error

        # 3. Validate against the available dates
        dates = plugin.get_dates(products, _location, start_at=date, end_at=date)
        if date not in dates:
            raise serializers.ValidationError(
                {"date": _("The selected date is not available (anymore).")}
            )

        # 4. Validate appointment start time against available time slots
        datetimes = plugin.get_times(products, _location, day=date)
        if attrs["datetime"] not in datetimes:
            raise serializers.ValidationError(
                {"datetime": _("The selected datetime is not available (anymore).")}
            )

        # 5. Validate contact details against product(s)
        contact_details_meta = plugin.get_required_customer_fields(products)
        contact_details_serializer = build_serializer(
            contact_details_meta,
            data=attrs["contact_details"],
            context={
                **self.context,
                "submission": attrs["submission"],
            },
        )
        if not contact_details_serializer.is_valid():
            errors = contact_details_serializer.errors
            raise serializers.ValidationError({"contact_details": errors})

        # expose additional metadata
        attrs.update(
            {
                "plugin": plugin.identifier,
                "contact_details_meta": contact_details_meta,
            }
        )
        return attrs

    @transaction.atomic
    def create(self, validated_data) -> Appointment:
        privacy_policy_accepted = validated_data.pop("privacy_policy_accepted")
        products = validated_data.pop("products")

        appointment = super().create(validated_data)

        appointment.submission.privacy_policy_accepted = privacy_policy_accepted

        # handle nested products
        appointment_products = [
            AppointmentProduct(appointment=appointment, **kwargs) for kwargs in products
        ]
        AppointmentProduct.objects.bulk_create(appointment_products)

        return appointment

    @extend_schema_field(OpenApiTypes.URI)
    def get_status_url(self, obj) -> str:
        return self.context["request"].build_absolute_uri(self._status_url)
