from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _

import requests

from openforms.config.data import Action
from openforms.plugins.exceptions import InvalidPluginConfiguration

from .clients import NoServiceConfigured, get_bag_client, get_locatieserver_client
from .models import KadasterApiConfig


class LocatieServerCheck:
    verbose_name: str = _("Kadaster API: locatieserver")  # type: ignore

    @staticmethod
    def check_config():
        try:
            with get_locatieserver_client() as client:
                client.free_address_search("Amsterdam", reraise_errors=True)
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
                    "admin:kadaster_kadasterapiconfig_change",
                    args=(KadasterApiConfig.singleton_instance_id,),
                ),
            ),
        ]


class BAGCheck:
    verbose_name: str = _("Kadaster API: BAG")  # type: ignore

    @staticmethod
    def check_config():
        try:
            with get_bag_client() as client:
                client.get_address("1000AA", "1", reraise_errors=True)
        except NoServiceConfigured as exc:
            msg = _("{api_name} endpoint is not configured").format(
                api_name="bag_service"
            )
            raise InvalidPluginConfiguration(msg) from exc
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
                    "admin:kadaster_kadasterapiconfig_change",
                    args=(KadasterApiConfig.singleton_instance_id,),
                ),
            ),
        ]
