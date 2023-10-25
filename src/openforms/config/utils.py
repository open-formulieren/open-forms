from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from django.contrib.admin.options import get_content_type_for_model
from django.db.models import Model

import clamd

from openforms.config.constants import ADDITIONAL_CSP_VALUES, CSPDirective
from openforms.payments.contrib.ogone.models import OgoneMerchant

if TYPE_CHECKING:  # pragma: nocover
    from digid_eherkenning.models.digid import DigidConfiguration
    from digid_eherkenning.models.eherkenning import EherkenningConfiguration


@dataclass
class ClamAVStatus:
    can_connect: bool
    error: str = ""


def verify_clamav_connection(host: str, port: int, timeout: int) -> "ClamAVStatus":
    scanner = clamd.ClamdNetworkSocket(
        host=host,
        port=port,
        timeout=timeout,
    )
    try:
        result = scanner.ping()
    except clamd.ConnectionError as exc:
        return ClamAVStatus(can_connect=False, error=exc.args[0])

    if result == "PONG":
        return ClamAVStatus(can_connect=True)

    return ClamAVStatus(can_connect=False, error=result)


def _create_csp_settings(obj: Model, directive: str, value: str) -> None:
    from .models import CSPSetting

    CSPSetting.objects.filter(
        content_type=get_content_type_for_model(obj), object_id=str(obj.id)
    ).delete()

    CSPSetting.objects.create(content_object=obj, directive=directive, value=value)


def create_digid_eherkenning_csp_settings(
    config: Union["DigidConfiguration", "EherkenningConfiguration"], config_type: str
) -> None:
    if not config.metadata_file_source:
        return

    # create the new directives based on the POST bindings of the metadata XML and
    # the additional constants
    urls, _ = config.process_metadata_from_xml_source()
    if ADDITIONAL_CSP_VALUES[config_type]:
        urls = (
            f"{ADDITIONAL_CSP_VALUES[config_type]} {urls['sso_url']} {urls['slo_url']}"
        )
    else:
        urls = f"{urls['sso_url']} {urls['slo_url']}"

    _create_csp_settings(config, CSPDirective.FORM_ACTION, urls)


def create_ogone_csp_settings(
    merchant: OgoneMerchant, directive: str, value: str
) -> None:
    _create_csp_settings(merchant, directive, value)
