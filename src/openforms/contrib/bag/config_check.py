from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _

import requests

from openforms.config.data import Action
from openforms.plugins.exceptions import InvalidPluginConfiguration

from .client import NoServiceConfigured, get_client
from .models import BAGConfig


class Check:
    verbose_name: str = _("BAG")  # type: ignore

    @staticmethod
    def check_config():
        try:
            client = get_client()
        except NoServiceConfigured as exc:
            msg = _("{api_name} endpoint is not configured.").format(
                api_name="bag_service"
            )
            raise InvalidPluginConfiguration(msg) from exc

        try:
            with client:
                client.get_address("1000AA", "1", reraise_errors=True)
        except requests.RequestException as exc:
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=exc)
            ) from exc

    @staticmethod
    def get_config_actions() -> list[Action]:
        return [
            (
                gettext("Configuration"),
                reverse(
                    "admin:bag_bagconfig_change",
                    args=(BAGConfig.singleton_instance_id,),
                ),
            ),
        ]
