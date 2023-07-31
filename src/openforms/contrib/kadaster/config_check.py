from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _

from requests import HTTPError
from zds_client import ClientError

from openforms.config.data import Action
from openforms.plugins.exceptions import InvalidPluginConfiguration

from .models import KadasterApiConfig
from .search import free_address_search


class Check:
    verbose_name: str = _("Kadaster API")  # type: ignore

    @staticmethod
    def check_config():
        config = KadasterApiConfig.get_solo()
        assert isinstance(config, KadasterApiConfig)

        client = config.get_client()
        try:
            free_address_search(client, "Amsterdam")
        except (HTTPError, ClientError) as e:
            e = e.__cause__ or e
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=e)
            )

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
