from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_camunda.client import get_client
from django_camunda.models import CamundaConfig

from openforms.plugins.exceptions import InvalidPluginConfiguration


def check_config(plugin):
    # maybe: introspect permissions -> check that client can start instances
    config = CamundaConfig.get_solo()

    if not config.enabled:
        raise InvalidPluginConfiguration(
            _("Camunda integration is not enabled in the configuration.")
        )

    try:
        config.clean()
    except ValidationError as error:
        raise InvalidPluginConfiguration(
            _("Configuration did not validate, see below.\n\n{msg}").format(
                msg=error.message
            )
        )

    with get_client():
        try:
            num_defs = len(plugin.get_available_decision_definitions())
        except Exception as exc:
            raise InvalidPluginConfiguration(
                _("Could not retrieve the available decision definitions.")
            ) from exc

        if num_defs <= 0:
            raise InvalidPluginConfiguration(
                _(
                    "No decision definitions found. The Camunda user may not have sufficient permissions."
                )
            )
