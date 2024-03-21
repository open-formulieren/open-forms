import logging
from datetime import date
from typing import Protocol

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.utils.html import format_html
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.request import Request

from openforms.authentication.constants import AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.submissions.models import Submission
from openforms.typing import DataMapping
from openforms.utils.date import format_date_value
from openforms.utils.validators import BSNValidator
from openforms.validations.service import PluginValidator

from ..dynamic_config.date import mutate as mutate_min_max_validation
from ..formatters.custom import (
    AddressNLFormatter,
    DateFormatter,
    DateTimeFormatter,
    MapFormatter,
)
from ..formatters.formio import DefaultFormatter, TextFieldFormatter
from ..registry import BasePlugin, register
from ..typing import Component, DateComponent, DatetimeComponent
from ..utils import conform_to_mask
from .np_family_members.constants import FamilyMembersDataAPIChoices
from .np_family_members.haal_centraal import get_np_family_members_haal_centraal
from .np_family_members.models import FamilyMembersTypeConfig
from .np_family_members.stuf_bg import get_np_family_members_stuf_bg
from .utils import _normalize_pattern

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
            validators.append(MinValueValidator(date.fromisoformat(min_date)))
        if max_date := date_picker.get("maxDate"):
            validators.append(MaxValueValidator(date.fromisoformat(max_date)))
        base = FormioDateField(
            required=required,
            allow_null=not required,
            validators=validators,
        )
        return serializers.ListField(child=base) if multiple else base


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


@register("map")
class Map(BasePlugin[Component]):
    formatter = MapFormatter

    @staticmethod
    def rewrite_for_request(component, request: Request):
        if component.get("useConfigDefaultMapSettings", False):
            config = GlobalConfiguration.get_solo()
            assert isinstance(config, GlobalConfiguration)
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
        return serializers.ListField(child=base)


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
            validators += [PluginValidator(plugin) for plugin in plugin_ids]

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
            validators += [PluginValidator(plugin) for plugin in plugin_ids]

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


@register("addressNL")
class AddressNL(BasePlugin):

    formatter = AddressNLFormatter
