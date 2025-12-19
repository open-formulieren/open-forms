from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
import structlog

from openforms.authentication.service import AuthAttribute
from openforms.contrib.customer_interactions.client import (
    get_customer_interactions_client,
)
from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)
from openforms.contrib.customer_interactions.transform import (
    transform_digital_addresses,
)
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission, SubmissionValueVariable
from openforms.typing import JSONEncodable, JSONObject

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...exceptions import PrefillSkipped
from ...registry import register
from .config import CommunicationPreferencesSerializer
from .constants import PLUGIN_IDENTIFIER
from .typing import CommunicationPreferencesOptions

logger = structlog.stdlib.get_logger(__name__)


@register(PLUGIN_IDENTIFIER)
class CommunicationPreferences(BasePlugin[CommunicationPreferencesOptions]):
    verbose_name = _("Communication preferences (customer interactions API)")
    requires_auth = (AuthAttribute.bsn,)
    options = CommunicationPreferencesSerializer

    @classmethod
    def get_prefill_values_from_options(
        cls,
        submission: Submission,
        options: CommunicationPreferencesOptions,
        submission_value_variable: SubmissionValueVariable,
    ) -> dict[str, JSONEncodable]:
        if not (
            bsn_value := cls.get_identifier_value(
                submission, identifier_role=IdentifierRoles.main
            )
        ):
            logger.info(
                "lookup_identifier_absent",
                submission_uuid=str(submission.uuid),
                plugin=cls,
            )
            raise PrefillSkipped("No BSN available.")

        assert submission_value_variable.form_variable
        prefill_variable = str(submission_value_variable.form_variable.key)
        profile_form_variable = options["profile_form_variable"]

        # use component variable to find a formio component
        total_config_wrapper = submission.total_configuration_wrapper
        profile_component = total_config_wrapper[profile_form_variable]
        assert profile_component["type"] == "customerProfile"
        if not (address_types := profile_component.get("digitalAddressTypes")):
            logger.info(
                "missing_component_digital_address_types",
                submission_uuid=str(submission.uuid),
                plugin=cls,
                component=profile_component,
            )
            raise PrefillSkipped("No 'digitalAddressTypes' available in the component.")

        with get_customer_interactions_client(
            options["customer_interactions_api_group"]
        ) as client:
            digital_addresses = client.get_digital_addresses_for_bsn(bsn=bsn_value)

        result = transform_digital_addresses(digital_addresses, address_types)
        return {prefill_variable: result}  # pyright: ignore[reportReturnType]

    def check_config(self):
        for config in CustomerInteractionsAPIGroupConfig.objects.iterator():
            try:
                with get_customer_interactions_client(config) as client:
                    resp = client.get("")
                    resp.raise_for_status()

            except requests.RequestException as exc:
                raise InvalidPluginConfiguration(
                    _("Client error: {exception}").format(exception=exc)
                ) from exc

    def get_config_actions(self):
        return [
            (
                _("Manage API groups"),
                reverse(
                    "admin:customer_interactions_customerinteractionsapigroupconfig_changelist",
                ),
            ),
        ]

    @classmethod
    def configuration_context(cls) -> JSONObject | None:
        return {
            "api_groups": [
                [group.identifier, group.name]
                for group in CustomerInteractionsAPIGroupConfig.objects.iterator()
            ]
        }
