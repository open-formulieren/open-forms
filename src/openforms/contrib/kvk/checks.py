from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _

import requests

from openforms.config.data import Action
from openforms.plugins.exceptions import InvalidPluginConfiguration

from .client import NoServiceConfigured, get_kvk_search_client
from .models import KVKConfig


class KVKRemoteValidatorCheck:
    verbose_name: str = _("Validation plugin config: KVK numbers")  # type: ignore

    @staticmethod
    def check_config():
        check_kvk = "68750110"
        try:
            with get_kvk_search_client() as client:
                results = client.get_search_results({"kvkNummer": check_kvk})
        except NoServiceConfigured as exc:
            msg = _("{api_name} endpoint is not configured.").format(api_name="KVK")
            raise InvalidPluginConfiguration(msg) from exc
        except requests.RequestException as exc:
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=exc)
            ) from exc

        if not isinstance(results, dict):
            raise InvalidPluginConfiguration(_("Response data is not a dictionary"))

        items = results.get("resultaten")
        if not items or not isinstance(items, list):
            raise InvalidPluginConfiguration(_("Response does not contain results"))

        num = items[0].get("kvkNummer", None)
        if num != check_kvk:
            msg = _("Did not find kvkNummer='{kvk}' in results").format(kvk=check_kvk)
            raise InvalidPluginConfiguration(msg)

    @staticmethod
    def get_config_actions() -> list[Action]:
        return [
            (
                gettext("Configuration"),
                reverse(
                    "admin:kvk_kvkconfig_change",
                    args=(KVKConfig.singleton_instance_id,),
                ),
            ),
        ]
