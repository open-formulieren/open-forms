import logging
from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _

from glom import GlomError, glom
from requests import RequestException
from zds_client import ClientError

from openforms.authentication.constants import AuthAttribute
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...registry import register
from .constants import Attributes
from .models import HaalCentraalConfig

logger = logging.getLogger(__name__)


@register("haalcentraal")
class HaalCentraalPrefill(BasePlugin):
    verbose_name = _("Haal Centraal")
    requires_auth = AuthAttribute.bsn

    @staticmethod
    def get_available_attributes():
        return Attributes.choices

    @staticmethod
    def get_prefill_values(
        submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        if not submission.bsn:
            return {}

        config = HaalCentraalConfig.get_solo()
        if not config.service:
            logger.warning("no service defined for Haal Centraal prefill")
            return {}

        client = config.service.build_client()

        try:
            data = client.retrieve(
                "ingeschrevenpersonen",
                burgerservicenummer=submission.bsn,
                request_kwargs=dict(headers={"Accept": "application/hal+json"}),
            )
        except RequestException as e:
            logger.exception("exception while making request", exc_info=e)
            return {}
        except ClientError as e:
            logger.exception("exception while making request", exc_info=e)
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

    def test_config(self):
        return True
