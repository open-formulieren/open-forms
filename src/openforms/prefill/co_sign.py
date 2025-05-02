"""
Integrate pre-fill functionality with co-sign authentication flow.

When a user authenticates to co-sign a submission, we need to retrieve information
based on their identifier to get a representation of the co-signer for the UI. This is
done by amending the co-sign data on a submission when the co-sign auth event is
received, see the :mod:`signals` module.
"""

import structlog

from openforms.authentication.service import AuthAttribute
from openforms.submissions.cosigning import CosignV1Data
from openforms.submissions.models import Submission

from .models import PrefillConfig
from .registry import register

logger = structlog.stdlib.get_logger(__name__)


AUTH_ATTRIBUTE_TO_CONFIG_FIELD = {
    AuthAttribute.bsn: "default_person_plugin",
    AuthAttribute.kvk: "default_company_plugin",
}


def get_default_plugin_for_auth_attribute(
    auth_attribute: AuthAttribute | None,
) -> str | None:
    if not auth_attribute or not (
        config_field := AUTH_ATTRIBUTE_TO_CONFIG_FIELD.get(auth_attribute)
    ):
        logger.info(
            "unsupported_auth_attribute_provided", auth_attribute=auth_attribute
        )
        return

    config = PrefillConfig.get_solo()
    default_plugin = getattr(config, config_field)
    if not default_plugin:
        logger.info("missing_prefill_config", field=config_field)
    return default_plugin


def add_co_sign_representation(
    submission: Submission, auth_attribute: AuthAttribute | None
):
    log = logger.bind(
        action="prefill.add_co_sign_representation",
        submission_uuid=str(submission.uuid),
    )
    default_plugin = get_default_plugin_for_auth_attribute(auth_attribute)
    # configuration may be incomplete, do nothing in that case!
    if not default_plugin:
        log.debug("no_lookup_plugin")
        return

    plugin = register[default_plugin]
    log = log.bind(plugin=plugin)

    _cosign_data: CosignV1Data = submission.co_sign_data.copy()

    log.debug("retrieving_cosign_representation")
    values, representation = plugin.get_co_sign_values(
        submission, _cosign_data["identifier"]
    )
    _cosign_data.update(
        {
            "fields": values,
            "representation": representation,
        }
    )
    submission.co_sign_data.update(_cosign_data)
    submission.save(update_fields=["co_sign_data"])
    log.debug("cosign_data_updated")
