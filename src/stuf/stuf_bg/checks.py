from django.utils.translation import gettext_lazy as _

import requests
from lxml import etree

from .client import NoServiceConfigured, get_client
from .exceptions import InvalidPluginConfiguration
from .utils import fromstring


def is_object_not_found_response(xml):
    faults = xml.xpath("//*[local-name()='Fault']/faultstring")
    if not faults or faults[0].text != "Object niet gevonden":
        return False
    else:
        return True


def is_empty_wrapped_response(xml):
    meta = xml.xpath("//*[local-name()='Body']/*/*[local-name()='stuurgegevens']")
    response = xml.xpath("//*[local-name()='Body']/*/*[local-name()='antwoord']")
    if meta and not response:
        return True
    else:
        return False


def check_config():
    check_bsn = "111222333"
    try:
        with get_client() as client:
            response = client.templated_request(
                "npsLv01",
                template="stuf_bg/StufBgRequest.xml",
                context={"bsn": check_bsn},
            )
            response.raise_for_status()
    except NoServiceConfigured as exc:
        raise InvalidPluginConfiguration(_("Service not selected")) from exc
    except requests.RequestException as exc:
        raise InvalidPluginConfiguration(
            _("Client error: {exception}").format(exception=exc)
        ) from exc

    try:
        xml = fromstring(response.content)
    except etree.XMLSyntaxError as exc:
        raise InvalidPluginConfiguration(
            _("SyntaxError in response: {exception}").format(exception=exc)
        ) from exc

    # we expect a valid 'object not found' response,
    #   but also accept an empty response (for 3rd party backend implementation reasons)
    if not is_object_not_found_response(xml) and not is_empty_wrapped_response(xml):
        raise InvalidPluginConfiguration(
            _("Unexpected response: expected '{message}' SOAP response").format(
                message="Object niet gevonden"
            )
        )
