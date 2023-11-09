from typing import Dict

from django.templatetags.static import static

from digid_eherkenning.models import DigidConfiguration, EherkenningConfiguration
from onelogin.saml2.constants import OneLogin_Saml2_Constants
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser

from openforms.authentication.constants import LogoAppearance
from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting

from .constants import ADDITIONAL_CSP_VALUES


def get_digid_logo(request) -> Dict[str, str]:
    return {
        "image_src": request.build_absolute_uri(static("img/digid-46x46.png")),
        "href": "https://www.digid.nl/",
        "appearance": LogoAppearance.dark,
    }


def get_eherkenning_logo(request) -> Dict[str, str]:
    return {
        "image_src": request.build_absolute_uri(static("img/eherkenning.png")),
        "href": "https://www.eherkenning.nl/",
        "appearance": LogoAppearance.light,
    }


def get_form_action_urls(
    config: DigidConfiguration | EherkenningConfiguration,
) -> list[str] | None:
    """
    Extract the <form> post action URLs from the configuration IDP metadata.

    This is a slightly altered version of the config.process_metadata_from_xml_source
    method which takes into account existing metadata without configured source.
    """
    if not config.idp_metadata_file:
        return None

    with config.idp_metadata_file.open("r") as infile:
        xml_metadata = infile.read()

    parsed_idp_metadata = OneLogin_Saml2_IdPMetadataParser.parse(
        xml_metadata,
        required_sso_binding=OneLogin_Saml2_Constants.BINDING_HTTP_POST,
        required_slo_binding=OneLogin_Saml2_Constants.BINDING_HTTP_POST,
    )
    if not (idp := parsed_idp_metadata.get("idp")):
        return None

    urls = []
    for key in ("singleSignOnService", "singleLogoutService"):
        if url := idp.get(key, {}).get("url"):
            urls.append(url)

    return urls


def create_digid_eherkenning_csp_settings(
    config: DigidConfiguration | EherkenningConfiguration,
) -> None:
    # create the new directives based on the POST bindings of the metadata XML and
    # the additional constants

    urls = get_form_action_urls(config)
    if not urls:
        return

    if additional_csp_values := ADDITIONAL_CSP_VALUES.get(type(config), ""):
        urls.append(additional_csp_values)

    form_action_urls = " ".join(urls)
    CSPSetting.objects.set_for(config, [(CSPDirective.FORM_ACTION, form_action_urls)])
