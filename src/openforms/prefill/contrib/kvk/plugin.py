import logging
from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _

from glom import GlomError, glom
from requests import RequestException
from zds_client import ClientError

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.kvk.client import KVKClient, KVKClientError
from openforms.submissions.models import Submission
from openforms.contrib.kvk.models import KVKConfig

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

    def test_config(self):
        config = KVKConfig.get_solo()

        if not config.service:
            return ['Geen service gedefinieerd voor KvK client']

        client = config.service.build_client()
        try:
            data = client.retrieve(client, client.base_url)
            print('kvk client', data)
        except Exception as e:
            return [str(e)]

        return True
