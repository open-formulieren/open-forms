import logging
import re
from datetime import datetime
from typing import Protocol

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.html import format_html
from django.utils.translation import gettext as _

from glom import glom
from rest_framework import ISO_8601, serializers
from rest_framework.request import Request

from openforms.authentication.service import AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.submissions.models import Submission
from openforms.typing import DataMapping
from openforms.utils.date import TIMEZONE_AMS, datetime_in_amsterdam, format_date_value
from openforms.utils.validators import BSNValidator, IBANValidator
from openforms.validations.service import PluginValidator

from ..dynamic_config.date import mutate as mutate_min_max_validation
from ..formatters.custom import (
    AddressNLFormatter,
    CosignFormatter,
    DateFormatter,
    DateTimeFormatter,
    MapFormatter,
)
from ..formatters.formio import DefaultFormatter, TextFieldFormatter
from ..registry import BasePlugin, register
from ..typing import AddressNLComponent, Component, DateComponent, DatetimeComponent
from ..utils import conform_to_mask
from .np_family_members.constants import FamilyMembersDataAPIChoices
from .np_family_members.haal_centraal import get_np_family_members_haal_centraal
from .np_family_members.models import FamilyMembersTypeConfig
from .np_family_members.stuf_bg import get_np_family_members_stuf_bg
from .utils import _normalize_pattern, salt_location_message

logger = logging.getLogger(__name__)


class FormioDateField(serializers.DateField):
    def validate_empty_values(self, data):
        is_empty, data = super().validate_empty_values(data)
        # base field only treats `None` as empty, but formio uses empty strings
        if data == "":
            if self.required:
                self.fail("required")
            return (True, "")
        return is_empty, data


@register("date")
class Date(BasePlugin[DateComponent]):
    formatter = DateFormatter

    @staticmethod
    def normalizer(component: DateComponent, value: str) -> str:
        return format_date_value(value)

    def mutate_config_dynamically(
        self, component: DateComponent, submission: Submission, data: DataMapping
    ) -> None:
        """
        Implement the behaviour for our custom date component options.

        In the JS, this component type inherits from Formio datetime component. See
        ``src/openforms/js/components/form/date.js`` for the various configurable options.
        """
        mutate_min_max_validation(component, data)

    def build_serializer_field(
        self, component: DateComponent
    ) -> FormioDateField | serializers.ListField:
        """
        Accept date values.

        Additional validation is taken from the datePicker configuration, which is also
        set dynamically through our own backend (see :meth:`mutate_config_dynamically`).
        """
        # relevant validators: required, datePicker.minDate and datePicker.maxDate
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)
        date_picker = component.get("datePicker") or {}
        validators = []

        if min_date := date_picker.get("minDate"):
            min_value = datetime_in_amsterdam(datetime.fromisoformat(min_date)).date()
            validators.append(MinValueValidator(min_value))

        if max_date := date_picker.get("maxDate"):
            max_value = datetime_in_amsterdam(datetime.fromisoformat(max_date)).date()
            validators.append(MaxValueValidator(max_value))

        base = FormioDateField(
            required=required,
            allow_null=not required,
            validators=validators,
        )
        return serializers.ListField(child=base) if multiple else base


class FormioDateTimeField(serializers.DateTimeField):
    def validate_empty_values(self, data):
        is_empty, data = super().validate_empty_values(data)
        # base field only treats `None` as empty, but formio uses empty strings
        if data == "":
            if self.required:
                self.fail("required")
            return (True, "")
        return is_empty, data

    def to_internal_value(self, value):
        # we *only* accept datetimes in ISO-8601 format. Python will happily parse a
        # YYYY-MM-DD string as a datetime (with hours/minutes set to 0). For a component
        # specifically aimed at datetimes, this is not a valid input.
        if value and isinstance(value, str) and "T" not in value:
            self.fail("invalid", format="YYYY-MM-DDTHH:mm:ss+XX:YY")
        return super().to_internal_value(value)


def _normalize_validation_datetime(value: str) -> datetime:
    """
    Takes a string expected to contain an ISO-8601 datetime and normalizes it.

    Seconds and time zone information may be missing. If it is, assume Europe/Amsterdam.

    :return: Time-zone aware datetime.
    """
    parsed = datetime.fromisoformat(value)
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone=TIMEZONE_AMS)
    return parsed


@register("datetime")
class Datetime(BasePlugin):
    formatter = DateTimeFormatter

    def mutate_config_dynamically(
        self,
        component: DatetimeComponent,
        submission: Submission,
        data: DataMapping,
    ) -> None:
        """
        Implement the behaviour for our custom datetime component options.
        """
        mutate_min_max_validation(component, data)

    def build_serializer_field(
        self, component: DateComponent
    ) -> FormioDateTimeField | serializers.ListField:
        """
        Accept datetime values.

        Additional validation is taken from the datePicker configuration, which is also
        set dynamically through our own backend (see :meth:`mutate_config_dynamically`).
        """
        # relevant validators: required, datePicker.minDate and datePicker.maxDate
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)
        date_picker = component.get("datePicker") or {}
        validators = []

        if min_date := date_picker.get("minDate"):
            min_value = _normalize_validation_datetime(min_date)
            validators.append(MinValueValidator(min_value))

        if max_date := date_picker.get("maxDate"):
            max_value = _normalize_validation_datetime(max_date)
            validators.append(MaxValueValidator(max_value))

        base = FormioDateTimeField(
            input_formats=[ISO_8601],
            required=required,
            allow_null=not required,
            validators=validators,
        )
        return serializers.ListField(child=base) if multiple else base


@register("map")
class Map(BasePlugin[Component]):
    formatter = MapFormatter

    @staticmethod
    def rewrite_for_request(component, request: Request):
        if component.get("useConfigDefaultMapSettings", False):
            config = GlobalConfiguration.get_solo()
            component["defaultZoom"] = config.form_map_default_zoom_level
            component.setdefault("initialCenter", {})
            component["initialCenter"]["lat"] = config.form_map_default_latitude
            component["initialCenter"]["lng"] = config.form_map_default_longitude

    def build_serializer_field(self, component: Component) -> serializers.ListField:
        validate = component.get("validate", {})
        required = validate.get("required", False)
        base = serializers.FloatField(
            required=required,
            allow_null=not required,
        )
        return serializers.ListField(child=base, min_length=2, max_length=2)


@register("postcode")
class Postcode(BasePlugin[Component]):
    formatter = TextFieldFormatter

    @staticmethod
    def normalizer(component: Component, value: str) -> str:
        if not value:
            return value

        input_mask = component.get("inputMask")
        if not input_mask:
            return value

        try:
            return conform_to_mask(value, input_mask)
        except ValueError:
            logger.warning(
                "Could not conform value '%s' to input mask '%s', returning original value."
            )
            return value

    def build_serializer_field(
        self, component: Component
    ) -> serializers.CharField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)
        # dynamically add in more kwargs based on the component configuration
        extra = {}
        validators = []
        # adding in the validator is more explicit than changing to serialiers.RegexField,
        # which essentially does the same.
        if pattern := validate.get("pattern"):
            validators.append(
                RegexValidator(
                    _normalize_pattern(pattern),
                    message=_("This value does not match the required pattern."),
                )
            )

        if plugin_ids := validate.get("plugins", []):
            validators.append(PluginValidator(plugin_ids))

        if validators:
            extra["validators"] = validators

        base = serializers.CharField(
            required=required, allow_blank=not required, **extra
        )
        return serializers.ListField(child=base) if multiple else base


class FamilyMembersHandler(Protocol):
    def __call__(
        self,
        bsn: str,
        include_children: bool,
        include_partner: bool,
        submission: Submission | None = ...,
    ) -> list[tuple[str, str]]: ...


@register("npFamilyMembers")
class NPFamilyMembers(BasePlugin):
    # not actually relevant, as we transform the component into a different type
    formatter = DefaultFormatter

    @staticmethod
    def _get_handler() -> FamilyMembersHandler:
        handlers = {
            FamilyMembersDataAPIChoices.haal_centraal: get_np_family_members_haal_centraal,
            FamilyMembersDataAPIChoices.stuf_bg: get_np_family_members_stuf_bg,
        }
        config = FamilyMembersTypeConfig.get_solo()
        return handlers[config.data_api]

    def mutate_config_dynamically(
        self, component: Component, submission: Submission, data: DataMapping
    ) -> None:
        # Check authentication details/status before proceeding
        has_bsn = (
            submission.is_authenticated
            and submission.auth_info.attribute == AuthAttribute.bsn
        )
        if not has_bsn:
            component.update(
                {
                    "type": "content",
                    "html": format_html(
                        "<p>{message}</p>",
                        message=_(
                            "Selecting family members is currently not available."
                        ),
                    ),
                    "input": False,
                }
            )
            return

        bsn = submission.auth_info.value

        component.update(
            {
                "type": "selectboxes",
                "fieldSet": False,
                "inline": False,
                "inputType": "checkbox",
            }
        )

        if "mask" in component:
            del component["mask"]

        existing_values = component.get("values", [])
        empty_option = {
            "label": "",
            "value": "",
        }
        if not existing_values or existing_values[0] == empty_option:
            handler = self._get_handler()
            # make the API call
            # TODO: this should eventually be replaced with logic rules/variables that
            # retrieve data from an "arbitrary source", which will cause the data to
            # become available in the ``data`` argument instead.
            child_choices = handler(
                bsn,
                include_children=component.get("includeChildren", True),
                include_partners=component.get("includePartners", True),
                submission=submission,
            )

            component["values"] = [
                {
                    "label": label,
                    "value": value,
                }
                for value, label in child_choices
            ]


@register("productPrice")
class ProductPrice(BasePlugin):
    # not actually relevant, as we transform the component into a different type
    formatter = DefaultFormatter

    def mutate_config_dynamically(
        self, component: Component, submission: Submission, data: DataMapping
    ) -> None:

        component.update(
            {
                "type": "radio",
                "fieldSet": False,
                "inline": False,
                "inputType": "radio",
                "validate": {"required": True},
            }
        )
        current_price = submission.form.product.open_producten_price
        if current_price:
            component["values"] = [
                {
                    "label": f"{option.description}: € {option.amount}",
                    "value": option.uuid,
                }
                for option in current_price.options.all()
            ]

        if not component["values"]:
            logger.warning("Product does not have price options.")
            # TODO: error?


@register("bsn")
class BSN(BasePlugin[Component]):
    formatter = TextFieldFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.CharField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        # dynamically add in more kwargs based on the component configuration
        extra = {}

        validators = [BSNValidator()]
        if plugin_ids := validate.get("plugins", []):
            validators.append(PluginValidator(plugin_ids))

        extra["validators"] = validators

        base = serializers.CharField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=multiple,
            **extra,
        )
        return serializers.ListField(child=base) if multiple else base


class AddressValueSerializer(serializers.Serializer):
    postcode = serializers.RegexField(
        "^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$",
    )
    houseNumber = serializers.RegexField(
        r"^\d{1,5}$",
    )
    houseLetter = serializers.RegexField("^[a-zA-Z]$", required=False, allow_blank=True)
    houseNumberAddition = serializers.RegexField(
        "^([a-z,A-Z,0-9]){1,4}$",
        required=False,
        allow_blank=True,
    )
    streetName = serializers.CharField(
        label=_("street name"),
        help_text=_("Derived street name"),
        required=False,
        allow_blank=True,
    )
    city = serializers.CharField(
        label=_("city"),
        help_text=_("Derived city"),
        required=False,
        allow_blank=True,
    )
    secretStreetCity = serializers.CharField(
        label=_("city and street name secret"),
        help_text=_("Secret for the combination of city and street name"),
        required=False,
        allow_blank=True,
    )

    def __init__(self, **kwargs):
        self.derive_address = kwargs.pop("derive_address", None)
        self.component = kwargs.pop("component", None)
        super().__init__(**kwargs)

    def validate_city(self, value: str) -> str:
        if city_regex := glom(
            self.component, "openForms.components.city.validate.pattern", default=""
        ):
            if not re.fullmatch(city_regex, value):
                raise serializers.ValidationError(
                    _("City does not match the specified pattern."),
                    code="invalid",
                )
        return value

    def validate_postcode(self, value: str) -> str:
        """Normalize the postcode so that it matches the regex from the BRK API."""
        if postcode_regex := glom(
            self.component, "openForms.components.postcode.validate.pattern", default=""
        ):
            if not re.fullmatch(postcode_regex, value):
                raise serializers.ValidationError(
                    _("Postcode does not match the specified pattern."),
                    code="invalid",
                )
        return value.upper().replace(" ", "")

    def validate(self, attrs):
        attrs = super().validate(attrs)

        city = attrs.get("city", "")
        street_name = attrs.get("streetName", "")

        if self.derive_address:
            existing_hmac = attrs.get("secretStreetCity", "")
            postcode = attrs.get("postcode", "")
            number = attrs.get("houseNumber", "")

            computed_hmac = salt_location_message(
                {
                    "postcode": postcode,
                    "number": number,
                    "city": city,
                    "street_name": street_name,
                }
            )

            if not constant_time_compare(existing_hmac, computed_hmac):
                raise serializers.ValidationError(
                    _("Invalid secret city - street name combination"),
                    code="invalid",
                )

        return attrs


@register("addressNL")
class AddressNL(BasePlugin[AddressNLComponent]):

    formatter = AddressNLFormatter

    def build_serializer_field(
        self, component: AddressNLComponent
    ) -> AddressValueSerializer:

        validate = component.get("validate", {})
        required = validate.get("required", False)

        extra = {}
        validators = []
        if plugin_ids := validate.get("plugins", []):
            validators.append(PluginValidator(plugin_ids))

        extra["validators"] = validators

        return AddressValueSerializer(
            derive_address=component["deriveAddress"],
            required=required,
            allow_null=not required,
            component=component,
            **extra,
        )


@register("cosign")
class Cosign(BasePlugin):
    formatter = CosignFormatter

    def build_serializer_field(self, component: Component) -> serializers.EmailField:
        validate = component.get("validate", {})
        required = validate.get("required", False)
        return serializers.EmailField(required=required, allow_blank=not required)


@register("iban")
class Iban(BasePlugin):
    formatter = DefaultFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.CharField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        base = serializers.CharField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=multiple,
            validators=[IBANValidator()],
        )
        return serializers.ListField(child=base) if multiple else base


@register("licenseplate")
class LicensePlate(BasePlugin):
    formatter = DefaultFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.CharField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        extra = {}
        validators = []
        # adding in the validator is more explicit than changing to serialiers.RegexField,
        # which essentially does the same.
        if pattern := validate.get("pattern"):
            validators.append(
                RegexValidator(
                    _normalize_pattern(pattern),
                    message=_("This value does not match the required pattern."),
                )
            )

        if validators:
            extra["validators"] = validators

        base = serializers.CharField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=multiple,
            **extra,
        )

        return serializers.ListField(child=base) if multiple else base
