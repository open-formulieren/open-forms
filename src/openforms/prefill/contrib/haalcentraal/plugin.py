import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from glom import GlomError, glom
from requests import RequestException
from zds_client import ClientError

from openforms.authentication.constants import AuthAttribute
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.pre_requests.clients import PreRequestClientContext
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...registry import register
from .constants import Attributes, HaalCentraalVersion
from .models import HaalCentraalConfig

logger = logging.getLogger(__name__)


@register("haalcentraal")
class HaalCentraalPrefill(BasePlugin):
    verbose_name = _("Haal Centraal")
    requires_auth = AuthAttribute.bsn

    request_kwargs = dict(headers={"Accept": "application/hal+json"})

    @staticmethod
    def get_available_attributes() -> list[tuple[str, str]]:
        return Attributes.choices

    def get_config():
        config = HaalCentraalConfig.get_solo()
        if not config.service:
            logger.warning("no service defined for Haal Centraal prefill")
            return
        return config

    @classmethod
    def _get_values_for_bsn(
        cls, submission: Submission, bsn: str, attributes: Iterable[str]
    ) -> Dict[str, Any]:
        config = cls.get_config()

        if config.version != HaalCentraalVersion.haalcentraal13:
            logger.warning("Service configed for the wrong version.")
            return {}

        if not config:
            return {}

        client = config.service.build_client()
        client.context = PreRequestClientContext(submission=submission)

        # manually build the URL, since HaalCentraal API spec & Open Personen have
        # mismatching operation IDs
        resource_url = f"ingeschrevenpersonen/{bsn}"

        try:
            data = client.retrieve(
                "ingeschrevenpersonen",
                burgerservicenummer=bsn,
                url=resource_url,
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

    @classmethod
    def _get_values_for_bsn_v2(
        cls, submission: Submission, bsn: str, attributes: Iterable[str]
    ) -> Dict[str, Any]:
        config = cls.get_config()
        print(config.version)

        if config.version != HaalCentraalVersion.haalcentraal20:
            logger.warning("Service configed for the wrong version.")
            return {}

        if not config:
            return {}

        client = config.service.build_client()
        client.context = PreRequestClientContext(submission=submission)

        # manually build the URL, since HaalCentraal API spec & Open Personen have
        # mismatching operation IDs
        resource_url = "personen"

        headers = {"headers": {"Content-Type": "application/json", "Accept": "*/*"}}

        recource_body = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": [bsn],
            "fields": attributes,
        }

        try:
            data = client.operation(
                "Personen",
                data=recource_body,
                url=resource_url,
                request_kwargs=headers,
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
                values[attr] = glom(data["personen"][0], attr)
            except GlomError:
                logger.warning(
                    f"missing expected attribute '{attr}' in backend response"
                )

        return values

    @classmethod
    def get_prefill_values(
        cls, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        if (
            not submission.is_authenticated
            or submission.auth_info.attribute != AuthAttribute.bsn
        ):
            #  If there is no bsn we can't prefill any values so just return
            logger.info("No BSN associated with submission, cannot prefill.")
            return {}
        config = cls.get_config()
        if not config:
            return {}

        match config.version:
            case HaalCentraalVersion.haalcentraal13:
                return cls._get_values_for_bsn(
                    submission, submission.auth_info.value, attributes
                )
            case HaalCentraalVersion.haalcentraal20:
                return cls._get_values_for_bsn_v2(
                    submission, submission.auth_info.value, attributes
                )

    @classmethod
    def get_co_sign_values(
        cls, identifier: str, submission: Optional["Submission"] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Given an identifier, fetch the co-sign specific values.

        The return value is a dict keyed by field name as specified in
        ``self.co_sign_fields``.

        :param identifier: the unique co-signer identifier used to look up the details
          in the prefill backend.
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.
        """
        config = cls.get_config()
        if not config:
            return {}

        get_values_args = (
            submission,
            identifier,
            (
                Attributes.naam_voornamen,
                Attributes.naam_voorvoegsel,
                Attributes.naam_geslachtsnaam,
                Attributes.naam_voorletters,
            ),
        )

        match config.version:
            case HaalCentraalVersion.haalcentraal13:
                return cls._get_values_for_bsn(
                    values=cls._get_values_for_bsn(get_values_args)
                )
            case HaalCentraalVersion.haalcentraal20:
                values = cls._get_values_for_bsn_v2(get_values_args)

        first_names = values.get(Attributes.naam_voornamen, "")
        first_letters = values.get(Attributes.naam_voorletters) or " ".join(
            [f"{name[0]}." for name in first_names.split(" ") if name]
        )
        representation_bits = [
            first_letters,
            values.get(Attributes.naam_voorvoegsel, ""),
            values.get(Attributes.naam_geslachtsnaam, ""),
        ]
        return (
            values,
            " ".join([bit for bit in representation_bits if bit]),
        )

    def check_config(self):
        try:
            config = HaalCentraalConfig.get_solo()
            if not config.service:
                raise InvalidPluginConfiguration(_("Service not selected"))

            client = config.service.build_client()
            client.retrieve("test", "test")
        except ClientError as e:
            if e.args[0].get("status") == 404:
                return
            raise InvalidPluginConfiguration(
                _("Client error: {exception}").format(exception=e)
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
