import logging
from typing import Any, Dict, List

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from glom import GlomError, glom
from requests import RequestException
from zds_client import ClientError

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.kvk.client import KVKClientError, KVKProfileClient
from openforms.contrib.kvk.models import KVKConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...registry import register
from .constants import Attributes

logger = logging.getLogger(__name__)


def _select_address(items, type_):
    if not items:
        return None
    for item in items:
        if item.get("type") == type_:
            return item
    return items[0]  # fall back to the first one


@register("kvk-kvknumber")
class KVK_KVKNumberPrefill(BasePlugin):
    verbose_name = _("KvK Company by KvK number")

    requires_auth = AuthAttribute.kvk

    def get_available_attributes(self):
        return Attributes.choices

    def get_prefill_values(
        self, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        # check if submission was logged in with the identifier we're interested
        if not submission.kvk:
            return {}

        client = KVKProfileClient()

        try:
            result = client.query(submission.kvk)
        except (RequestException, ClientError, KVKClientError):
            return {}

        self.modify_result(result)

        values = dict()
        for attr in attributes:
            try:
                values[attr] = glom(result, attr)
            except GlomError:
                logger.warning(
                    f"missing expected attribute '{attr}' in backend response"
                )
        return values

    @classmethod
    def modify_result(cls, result):
        # move the desired item from the unordered list to a know place
        address = _select_address(result["adressen"], "bezoekadres")
        if address:
            result["bezoekadres"] = address
        address = _select_address(result["adressen"], "correspondentieadres")
        if address:
            result["correspondentieadres"] = address

    def check_config(self):
        check_kvk = "68750110"
        try:
            client = KVKProfileClient()
            result = client.query(check_kvk)
        except KVKClientError as e:
            raise InvalidPluginConfiguration(
                _("Configuration error: {exception}").format(exception=e)
            )
        except ClientError as e:
            e = e.__cause__ or e
            raise InvalidPluginConfiguration(
                _("Client error: {exception}").format(exception=e)
            )
        except Exception as e:
            # pass it on
            raise
        else:
            if not isinstance(result, dict):
                raise InvalidPluginConfiguration(_("Response not a dictionary"))
            num = result.get("kvkNummer", None)
            if num != check_kvk:
                raise InvalidPluginConfiguration(
                    _("Did not find kvkNummer='{kvk}' in results").format(kvk=check_kvk)
                )

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:kvk_kvkconfig_change",
                    args=(KVKConfig.singleton_instance_id,),
                ),
            ),
        ]
