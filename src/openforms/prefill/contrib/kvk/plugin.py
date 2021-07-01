import logging
from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _

from glom import GlomError, glom
from requests import RequestException
from zds_client import ClientError

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.kvk.client import KVKClient, KVKClientError
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...registry import register
from .constants import Attributes

logger = logging.getLogger(__name__)


class KVKBasePrefill(BasePlugin):
    """
    base plugin for KVK companies prefill, need subclassing for specialisation
    """

    query_param = None
    submission_attr = None

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

        items = results["data"]["items"]
        if not items:
            return {}

        if len(items) > 1:
            logger.warning("multiple results for")
            return {}

        data = items[0]

        values = dict()
        for attr in attributes:
            try:
                values[attr] = glom(data, attr)
            except GlomError:
                logger.warning(
                    f"missing expected attribute '{attr}' in backend response"
                )
        return values

    def get_submission_attr(self, submission):
        assert self.submission_attr
        return getattr(submission, self.submission_attr)

    def get_query_param(self):
        assert self.query_param
        return self.query_param


@register("kvk-kvknumber")
class KVK_KVKNumberPrefill(KVKBasePrefill):
    verbose_name = _("KvK Company by KvK number")

    query_param = "kvkNumber"
    submission_attr = "kvk"
    requires_auth = AuthAttribute.kvk


# disabled for now
# @register("kvk-rsin")
class KVK_RSINPrefill(KVKBasePrefill):
    verbose_name = _("KvK Company by RSIN")

    query_param = "rsin"
    submission_attr = "rsin"
    requires_auth = AuthAttribute.rsin


# disabled for now
# @register("kvk-branchnumber")
class KVK_BranchNumberPrefill(KVKBasePrefill):
    verbose_name = _("KvK Company by Branch number")

    query_param = "branchNumber"
    submission_attr = "branchNumber"
    requires_auth = AuthAttribute.branchNumber
