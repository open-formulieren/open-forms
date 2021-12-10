import logging
from typing import Any, Dict, List

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from glom import GlomError, glom
from requests import RequestException
from zds_client import ClientError

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.kvk.client import KVKClient, KVKClientError
from openforms.contrib.kvk.models import KVKConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...registry import register
from .constants import Attributes

logger = logging.getLogger(__name__)


@register("kvk-kvknumber")
class KVK_KVKNumberPrefill(BasePlugin):
    verbose_name = _("KvK Company by KvK number")

    # the KVK api also supports lookup by RSIN and branchNumber but we only support kvkNumber
    query_param = "kvkNummer"
    submission_attr = "kvk"
    requires_auth = AuthAttribute.kvk

    def get_available_attributes(self):
        return Attributes.choices

    def get_prefill_values(
        self, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        # check if submission was logged in with the identifier we're interested
        if not self.get_submission_attr(submission):
            return {}

        client = KVKClient()

        try:
            results = client.query(
                **{self.get_query_param(): self.get_submission_attr(submission)}
            )
        except (RequestException, ClientError, KVKClientError):
            return {}

        data = self.select_item(results["resultaten"])
        if not data:
            return {}

        values = dict()
        for attr in attributes:
            try:
                values[attr] = glom(data, attr)
            except GlomError:
                logger.warning(
                    f"missing expected attribute '{attr}' in backend response"
                )
        return values

    def select_item(self, items):
        if not items:
            return None
        for item in items:
            if item.get("type") == "hoofdvestiging":
                return item
        return items[0]

    def get_submission_attr(self, submission):
        assert self.submission_attr
        return getattr(submission, self.submission_attr)

    def get_query_param(self):
        assert self.query_param
        return self.query_param

    def check_config(self):
        check_kvk = "68750110"
        try:
            client = KVKClient()
            results = client.query(kvkNummer=check_kvk)
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
            if not isinstance(results, dict):
                raise InvalidPluginConfiguration(_("Response not a dictionary"))
            items = results.get("resultaten")
            if not items or not isinstance(items, list):
                raise InvalidPluginConfiguration(_("Response does not contain results"))
            num = items[0].get("kvkNummer", None)
            if num != check_kvk:
                raise InvalidPluginConfiguration(
                    _("Did not find kvkNummer='{kvk}' in results").format(check_kvk)
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
