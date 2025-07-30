import re
from datetime import datetime
from typing import Protocol

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.html import format_html
from django.utils.translation import gettext as _

import structlog
from glom import glom
from rest_framework import ISO_8601, serializers
from rest_framework.request import Request

from openforms.api.geojson import (
    GeoJsonGeometryPolymorphicSerializer,
    GeoJsonGeometryTypes,
)
from openforms.authentication.service import AuthAttribute
from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration, MapTileLayer
from openforms.forms.models import FormVariable
from openforms.prefill.contrib.family_members.plugin import (
    PLUGIN_IDENTIFIER as FM_PLUGIN_IDENTIFIER,
)
from openforms.submissions.models import Submission
from openforms.typing import JSONObject
from openforms.utils.date import TIMEZONE_AMS, datetime_in_amsterdam, format_date_value
from openforms.utils.json_schema import GEO_JSON_COORDINATE_SCHEMAS, to_multiple
from openforms.utils.validators import BSNValidator, IBANValidator
from openforms.validations.service import PluginValidator
from openforms.variables.constants import FormVariableSources

from ..datastructures import FormioData
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
from ..typing import (
    AddressNLComponent,
    ChildrenComponent,
    Component,
    DateComponent,
    DatetimeComponent,
    MapComponent,
)
from ..utils import conform_to_mask
from .np_family_members.haal_centraal import get_np_family_members_haal_centraal
from .np_family_members.stuf_bg import get_np_family_members_stuf_bg
from .utils import _normalize_pattern, salt_location_message

logger = structlog.stdlib.get_logger(__name__)


GEO_JSON_TYPE_TO_INTERACTION = {
    GeoJsonGeometryTypes.point: "marker",
    GeoJsonGeometryTypes.polygon: "polygon",
    GeoJsonGeometryTypes.line_string: "polyline",
}

POSTCODE_REGEX = r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$"
HOUSE_NUMBER_REGEX = r"^\d{1,5}$"
HOUSE_LETTER_REGEX = r"^[a-zA-Z]$"
HOUSE_NUMBER_ADDITION_REGEX = r"^[a-zA-Z0-9]{1,4}$"


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
        self, component: DateComponent, submission: Submission, data: FormioData
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

    @staticmethod
    def as_json_schema(component: DateComponent) -> JSONObject:
        label = component.get("label", "Date")
        multiple = component.get("multiple", False)

        base = {"title": label, "format": "date", "type": "string"}
        return to_multiple(base) if multiple else base


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
        data: FormioData,
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

    @staticmethod
    def as_json_schema(component: Component) -> JSONObject:
        label = component.get("label", "Date time")
        multiple = component.get("multiple", False)

        base = {"title": label, "format": "date-time", "type": "string"}
        return to_multiple(base) if multiple else base


@register("map")
class Map(BasePlugin[MapComponent]):
    formatter = MapFormatter

    def mutate_config_dynamically(
        self, component: MapComponent, submission: Submission, data: FormioData
    ) -> None:
        if (identifier := component.get("tileLayerIdentifier")) is not None:
            tile_layer = MapTileLayer.objects.filter(identifier=identifier).first()
            if tile_layer is not None:
                # Add the tile layer url information
                component["tileLayerUrl"] = tile_layer.url

    @staticmethod
    def rewrite_for_request(component: MapComponent, request: Request):
        if component.get("useConfigDefaultMapSettings", False):
            config = GlobalConfiguration.get_solo()
            component["defaultZoom"] = config.form_map_default_zoom_level
            component.setdefault("initialCenter", {})
            component["initialCenter"]["lat"] = config.form_map_default_latitude
            component["initialCenter"]["lng"] = config.form_map_default_longitude

    def build_serializer_field(
        self, component: MapComponent
    ) -> GeoJsonGeometryPolymorphicSerializer:
        validate = component.get("validate", {})
        required = validate.get("required", False)

        return GeoJsonGeometryPolymorphicSerializer(
            required=required, allow_null=not required
        )

    @staticmethod
    def as_json_schema(component: MapComponent) -> JSONObject:
        label = component.get("label", "Map")
        interactions = component["interactions"]

        properties = [
            {
                "properties": {
                    "type": {"type": "string", "const": geometry_type},
                    "coordinates": GEO_JSON_COORDINATE_SCHEMAS[geometry_type],
                },
                "additionalProperties": False,
            }
            for geometry_type in GeoJsonGeometryTypes.values
            # Only include the schema of types that are allowed
            if interactions.get(GEO_JSON_TYPE_TO_INTERACTION[geometry_type], False)
        ]

        schema = {
            "title": label,
            "type": "object",
            "required": ["type", "coordinates"],
        }
        if len(properties) == 1:
            schema.update(properties[0])
        else:
            schema["oneOf"] = properties

        return schema


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
        except ValueError as exc:
            logger.warning(
                "formio.postcode_to_mask_failure",
                input_mask=input_mask,
                value=value,
                component=component,
                exc_info=exc,
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
        # adding in the validator is more explicit than changing to
        # serializers.RegexField, which essentially does the same.
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

    @staticmethod
    def as_json_schema(component: Component) -> JSONObject:
        label = component.get("label", "Postcode")
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})

        base = {
            "title": label,
            "type": "string",
            "pattern": validate.get("pattern", POSTCODE_REGEX),
        }
        return to_multiple(base) if multiple else base


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
        config = GlobalConfiguration.get_solo()
        return handlers[config.family_members_data_api]

    def mutate_config_dynamically(
        self, component: Component, submission: Submission, data: FormioData
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

    @staticmethod
    def as_json_schema(component: Component) -> JSONObject:
        # This component plugin is transformed into a SelectBoxes component, so a schema
        # is not relevant here
        raise NotImplementedError()


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

    @staticmethod
    def as_json_schema(component: Component) -> JSONObject:
        label = component.get("label", "BSN")
        multiple = component.get("multiple", False)

        base = {
            "title": label,
            "type": "string",
            "pattern": r"^\d{9}$",
            "format": "nl-bsn",
        }
        return to_multiple(base) if multiple else base


class AddressValueSerializer(serializers.Serializer):
    postcode = serializers.RegexField(POSTCODE_REGEX)
    houseNumber = serializers.RegexField(HOUSE_NUMBER_REGEX)
    houseLetter = serializers.RegexField(
        HOUSE_LETTER_REGEX, required=False, allow_blank=True
    )
    houseNumberAddition = serializers.RegexField(
        HOUSE_NUMBER_ADDITION_REGEX,
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

    @staticmethod
    def as_json_schema(component: AddressNLComponent) -> JSONObject:
        label = component.get("label", "Address NL")
        components = component.get("openForms", {}).get("components", {})
        postcode_validate = components.get("postcode", {}).get("validate", {})
        city_validate = components.get("city", {}).get("validate", {})

        base = {
            "title": label,
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "houseLetter": {"type": "string", "pattern": HOUSE_LETTER_REGEX},
                "houseNumber": {"type": "string", "pattern": HOUSE_NUMBER_REGEX},
                "houseNumberAddition": {
                    "type": "string",
                    "pattern": HOUSE_NUMBER_ADDITION_REGEX,
                },
                "postcode": {
                    "type": "string",
                    "pattern": postcode_validate.get("pattern", POSTCODE_REGEX),
                },
                "streetName": {"type": "string"},
            },
            "required": ["houseNumber", "postcode"],
        }

        if city_pattern := city_validate.get("pattern"):
            base["properties"]["city"]["pattern"] = city_pattern

        return base


class PartnerSerializer(serializers.Serializer):
    bsn = serializers.CharField(
        label=_("bsn"),
        max_length=9,
        help_text=_("The BSN of the partner"),
        validators=[BSNValidator()],
    )
    initials = serializers.CharField(
        label=_("initials"),
        help_text=_("The initials of the partner"),
        required=False,
        allow_blank=True,
    )
    affixes = serializers.CharField(
        label=_("affixes"),
        help_text=_("The affixes of the partner"),
        required=False,
        allow_blank=True,
    )
    lastName = serializers.CharField(
        label=_("last name"),
        help_text=_("The last name of the partner"),
        required=False,
        allow_blank=True,
    )
    dateOfBirth = serializers.DateField(
        label=_("date of birth"),
        help_text=_("The date of birth of the partner"),
        required=False,
    )

    def __init__(self, **kwargs):
        self.component = kwargs.pop("component", None)
        super().__init__(**kwargs)


class PartnerListField(serializers.Field):
    def __init__(self, component, **kwargs):
        self.component = component
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if not isinstance(data, list):
            raise serializers.ValidationError("Expected a list of partners.")

        serializer = PartnerSerializer(
            data=data,
            many=True,
            component=self.component,
        )
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        self.validate_list(validated)
        return validated

    def to_representation(self, value):
        return PartnerSerializer(value, many=True, component=self.component).data

    def validate_list(self, partners):
        component_key = self.component["key"]
        submission = self.context["submission"]
        prefill_data = submission.get_prefilled_data()

        fm_immutable_variable = FormVariable.objects.filter(
            source=FormVariableSources.user_defined,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options__mutable_data_form_variable=component_key,
            form=submission.form,
        ).first()
        if fm_immutable_variable:
            # we do not receive these fields from the frontend (since they are not used
            # for now) so we have to exclude them from the data that needs validation
            initial_value = [
                {
                    key: (
                        datetime.strptime(value, "%Y-%m-%d").date()
                        if key == "dateOfBirth"
                        else value
                    )
                    for key, value in partner.items()
                    if key not in ("dateOfBirthPrecision", "firstNames")
                }
                for partner in prefill_data[fm_immutable_variable.key]
            ]

            if initial_value and initial_value != partners:
                raise serializers.ValidationError(
                    "The family members prefill data may not be altered."
                )


@register("partners")
class Partners(BasePlugin[Component]):
    formatter = DefaultFormatter

    def build_serializer_field(self, component: Component) -> PartnerListField:
        return PartnerListField(component=component)

    @staticmethod
    def as_json_schema(component: Component) -> JSONObject:
        label = component.get("label", "Partners")
        schema = {
            "title": label,
            "type": "array",
            "items": {
                "type": "object",
                "required": ["bsn"],
                "properties": {
                    "bsn": {
                        "type": "string",
                        "pattern": r"^\d{9}$",
                        "format": "nl-bsn",
                    },
                    "initials": {"type": "string"},
                    "affixes": {"type": "string"},
                    "lastName": {"type": "string"},
                    "dateOfBirth": {"type": "string", "format": "date"},
                },
                "additionalProperties": False,
            },
        }

        return schema


class ChildSerializer(serializers.Serializer):
    bsn = serializers.CharField(
        label=_("bsn"),
        max_length=9,
        help_text=_("The BSN of the child"),
        validators=[BSNValidator()],
    )
    # Optional on purpose since we may not receive any data from the external source
    firstNames = serializers.CharField(
        label=_("firstNames"),
        help_text=_("The first names of the child"),
        required=False,
        allow_blank=True,
    )
    # Optional on purpose since we may not receive any data from the external source
    dateOfBirth = serializers.DateField(
        label=_("date of birth"),
        help_text=_("The date of birth of the child"),
        required=False,
    )
    selected = serializers.BooleanField(
        label=_("selected"),
        default=False,
        help_text=_(
            "Whether the child is selected by the user or not for further processing"
        ),
    )

    def __init__(self, **kwargs):
        self.component = kwargs.pop("component", None)
        super().__init__(**kwargs)


class ChildListField(serializers.Field):
    def __init__(self, component, **kwargs):
        self.component = component
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if not isinstance(data, list):
            raise serializers.ValidationError("Expected a list of children.")

        serializer = ChildSerializer(
            data=data,
            many=True,
            component=self.component,
        )
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        self.validate_list(validated)
        return validated

    def to_representation(self, value):
        return ChildSerializer(value, many=True, component=self.component).data

    def validate_list(self, children):
        component_key = self.component["key"]
        submission = self.context["submission"]
        prefill_data = submission.get_prefilled_data()

        fm_immutable_variable = FormVariable.objects.filter(
            source=FormVariableSources.user_defined,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options__mutable_data_form_variable=component_key,
            form=submission.form.id,
        ).first()

        if fm_immutable_variable:
            # we do not receive these fields from the frontend (since they are not used
            # for now) so we have to exclude them from the data that needs validation.
            initial_value = [
                {
                    key: (
                        datetime.strptime(value, "%Y-%m-%d").date()
                        if key == "dateOfBirth"
                        else value
                    )
                    for key, value in child.items()
                    if key
                    not in (
                        "dateOfBirthPrecision",
                        "lastName",
                        "affixes",
                        "initials",
                    )
                }
                for child in prefill_data[fm_immutable_variable.key]
            ]

            # We also receive the boolean `selected` which is set on the frontend and
            # therefore should not be part of the data for validation
            for child in children:
                child.pop("selected", None)

            if initial_value and initial_value != children:
                raise serializers.ValidationError(
                    "The family members prefill data may not be altered."
                )


@register("children")
class Children(BasePlugin[ChildrenComponent]):
    formatter = DefaultFormatter

    def build_serializer_field(self, component: ChildrenComponent) -> ChildListField:
        return ChildListField(component=component)

    @staticmethod
    def as_json_schema(component: ChildrenComponent) -> JSONObject:
        label = component.get("label", "Children")
        schema = {
            "title": label,
            "type": "array",
            "items": {
                "type": "object",
                "required": ["bsn"],
                "properties": {
                    "bsn": {
                        "type": "string",
                        "pattern": r"^\d{9}$",
                        "format": "nl-bsn",
                    },
                    "firstNames": {"type": "string"},
                    "dateOfBirth": {"type": "string", "format": "date"},
                },
                "additionalProperties": False,
            },
        }

        return schema


@register("cosign")
class Cosign(BasePlugin):
    formatter = CosignFormatter

    def build_serializer_field(self, component: Component) -> serializers.EmailField:
        validate = component.get("validate", {})
        required = validate.get("required", False)
        return serializers.EmailField(required=required, allow_blank=not required)

    @staticmethod
    def as_json_schema(component: Component) -> JSONObject:
        label = component.get("label", "Cosign email")

        base = {"title": label, "type": "string", "format": "email"}

        return base


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

    @staticmethod
    def as_json_schema(component: Component) -> JSONObject:
        label = component.get("label", "IBAN")
        multiple = component.get("multiple", False)

        # Reference: https://en.wikipedia.org/wiki/International_Bank_Account_Number#Structure
        base = {
            "title": label,
            "type": "string",
            "pattern": r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{30}$",
        }
        return to_multiple(base) if multiple else base


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
        # adding in the validator is more explicit than changing to
        # serializers.RegexField, which essentially does the same.
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

    @staticmethod
    def as_json_schema(component: Component) -> JSONObject:
        label = component.get("label", "License plate")
        multiple = component.get("multiple", False)

        # NOTE: the pattern does not take into account letters that are not allowed
        # by the government.
        base = {
            "title": label,
            "type": "string",
            "pattern": r"^[a-zA-Z0-9]{1,3}-[a-zA-Z0-9]{1,3}-[a-zA-Z0-9]{1,3}$",
        }
        return to_multiple(base) if multiple else base
