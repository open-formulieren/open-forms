from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
import structlog

from openforms.authentication.service import AuthAttribute
from openforms.contrib.klantinteracties.client import get_klantinteracties_client
from openforms.contrib.klantinteracties.models import KlantinteractiesConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission, SubmissionValueVariable
from openforms.typing import JSONEncodable

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...exceptions import PrefillSkipped
from ...registry import register
from .config import KlantInteractiesOptionsSerializer
from .typing import KlantInteractiesOptions
from .utils import transform_digital_addresses

logger = structlog.stdlib.get_logger(__name__)

PLUGIN_IDENTIFIER = "klantinteracties"


@register(PLUGIN_IDENTIFIER)
class klantinteractiesPlugin(BasePlugin[KlantInteractiesOptions]):
    verbose_name = _("Klantinteracties API")
    requires_auth = (AuthAttribute.bsn,)
    options = KlantInteractiesOptionsSerializer

    @classmethod
    def get_prefill_values_from_options(
        cls,
        submission: Submission,
        options: KlantInteractiesOptions,
        submission_value_variable: SubmissionValueVariable,
    ) -> dict[str, JSONEncodable]:
        try:
            client = get_klantinteracties_client()
        except AssertionError:
            logger.warning("klantinteracties_service_not_configured")
            return {}

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
        variable = str(submission_value_variable.form_variable.key)

        digital_addresses = client.get_digital_addresses_for_bsn(bsn=bsn_value)
        result = transform_digital_addresses(digital_addresses, options)
        return {variable: result}

    def check_config(self):
        try:
            with get_klantinteracties_client() as client:
                resp = client.get("klantcontacten")
                resp.raise_for_status()

        except requests.RequestException as exc:
            raise InvalidPluginConfiguration(
                _("Invalid response from Klantinteracties API: {exception}").format(
                    exception=exc
                )
            ) from exc
        except Exception as exc:
            raise InvalidPluginConfiguration(
                _("Could not connect to Klantinteracties API: {exception}").format(
                    exception=exc
                )
            ) from exc

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:klantinteracties_klantinteractiesconfig_change",
                    args=(KlantinteractiesConfig.singleton_instance_id,),
                ),
            ),
        ]
