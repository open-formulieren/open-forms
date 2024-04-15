from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _

import requests

from openforms.config.data import Action
from openforms.plugins.exceptions import InvalidPluginConfiguration

from .client import NoServiceConfigured, get_client
from .models import BRKConfig


class BRKValidatorCheck:
    verbose_name: str = _("Validation plugin config: BRK - Zakelijk gerechtigd")  # type: ignore

    @staticmethod
    def check_config():
        try:
            with get_client() as client:
                results = client.get_real_estate_by_address(
                    {"postcode": "1234AB", "huisnummer": "1"}
                )
        except NoServiceConfigured as exc:
            msg = _("{api_name} endpoint is not configured").format(api_name="KVK")
            raise InvalidPluginConfiguration(msg) from exc
        except requests.RequestException as exc:
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=exc)
            ) from exc

        if not isinstance(results, dict):
            raise InvalidPluginConfiguration(_("Response data is not a dictionary"))

        items = results.get("_embedded")
        if items is None or not isinstance(items, dict):
            raise InvalidPluginConfiguration(_("Response does not contain results"))

    @staticmethod
    def get_config_actions() -> list[Action]:
        return [
            (
                gettext("Configuration"),
                reverse(
                    "admin:brk_brkconfig_change",
                    args=(BRKConfig.singleton_instance_id,),
                ),
            ),
        ]
