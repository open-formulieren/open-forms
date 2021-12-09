import logging
from typing import Any, Dict, List

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from glom import GlomError, glom
from requests import RequestException
from zds_client import ClientError

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.kvk.models import KVKConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
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

    request_kwargs = dict(headers={"Accept": "application/hal+json"})

    @staticmethod
    def get_available_attributes():
        return Attributes.choices

    @classmethod
    def get_prefill_values(
        cls, submission: Submission, attributes: List[str]
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
                request_kwargs=cls.request_kwargs,
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

    def check_config(self):
        check_bsn = "111222333"
        try:
            config = HaalCentraalConfig.get_solo()
            if not config.service:
                raise InvalidPluginConfiguration(_("Service not selected"))

            client = config.service.build_client()
            client.retrieve(
                "ingeschrevenpersonen",
                burgerservicenummer=check_bsn,
                request_kwargs=self.request_kwargs,
            )
        except ClientError as e:
            e = e.__cause__ or e
            # we expect a 404 for this BSN
            response = getattr(e, "response", None)
            if not response or response.status != 404:
                raise InvalidPluginConfiguration(
                    _("Client error: {exception}").format(exception=e)
                )

            # also check the body JSON
            data = response.json()
            if data.get("status") != 404:
                raise InvalidPluginConfiguration(
                    _("Missing status 404 in response body")
                )
        else:
            # shouldn't happen
            raise InvalidPluginConfiguration(
                _("Check call unexpectedly succeeded for test BSN '{}'").format(
                    check_bsn
                )
            )

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:prefill_haalcentraal_haalcentraalconfig_change",
                    args=(HaalCentraalConfig.singleton_instance_id,),
                ),
            ),
        ]
