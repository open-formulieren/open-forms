import logging
from typing import Callable

from openforms.authentication.constants import AuthAttribute
from openforms.submissions.models import Submission
from openforms.typing import DataMapping
from openforms.utils.date import format_date_value

from ..dynamic_config.date import FormioDateComponent, mutate as mutate_date
from ..formatters.custom import DateFormatter, MapFormatter
from ..formatters.formio import DefaultFormatter, TextFieldFormatter
from ..registry import BasePlugin, register
from ..typing import Component
from ..utils import conform_to_mask
from .np_family_members.constants import FamilyMembersDataAPIChoices
from .np_family_members.haal_centraal import get_np_children_haal_centraal
from .np_family_members.models import FamilyMembersTypeConfig
from .np_family_members.stuf_bg import get_np_children_stuf_bg

logger = logging.getLogger(__name__)


@register("date")
class Date(BasePlugin):
    formatter = DateFormatter

    @staticmethod
    def normalizer(component: FormioDateComponent, value: str) -> str:
        return format_date_value(value)

    def mutate_config_dynamically(
        self, component: FormioDateComponent, submission: Submission, data: DataMapping
    ) -> None:
        """
        Implement the behaviour for our custom date component options.

        In the JS, this component type inherits from Formio datetime component. See
        ``src/openforms/js/components/form/date.js`` for the various configurable options.
        """
        mutate_date(component, data)


@register("map")
class Map(BasePlugin):
    formatter = MapFormatter


@register("postcode")
class Postcode(BasePlugin):
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


@register("npFamilyMembers")
class NPFamilyMembers(BasePlugin):
    # not actually relevant, as we transform the component into a different type
    formatter = DefaultFormatter

    @staticmethod
    def _get_handler() -> Callable[[str], list[tuple[str, str]]]:
        handlers = {
            FamilyMembersDataAPIChoices.haal_centraal: get_np_children_haal_centraal,
            FamilyMembersDataAPIChoices.stuf_bg: get_np_children_stuf_bg,
        }
        config = FamilyMembersTypeConfig.get_solo()
        return handlers[config.data_api]

    @classmethod
    def mutate_config_dynamically(
        cls, component: Component, submission: Submission, data: DataMapping
    ) -> None:
        # Check authentication details/status before proceeding
        if not submission.is_authenticated:
            raise RuntimeError("No authenticated person!")
        if submission.auth_info.attribute != AuthAttribute.bsn:
            raise RuntimeError("No BSN found in the authentication details.")

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
            handler = cls._get_handler()
            # make the API call
            # TODO: this should eventually be replaced with logic rules/variables that
            # retrieve data from an "arbitrary source", which will cause the data to
            # become available in the ``data`` argument instead.
            child_choices = handler(bsn)

            component["values"] = [
                {
                    "label": label,
                    "value": value,
                }
                for value, label in child_choices
            ]
