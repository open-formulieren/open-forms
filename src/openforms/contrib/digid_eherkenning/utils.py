from typing import Dict

from django.templatetags.static import static

from digid_eherkenning.models import DigidConfiguration, EherkenningConfiguration

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


def create_digid_eherkenning_csp_settings(
    config: DigidConfiguration | EherkenningConfiguration,
) -> None:
    if not config.metadata_file_source:
        return

    # create the new directives based on the POST bindings of the metadata XML and
    # the additional constants
    urls, _ = config.process_metadata_from_xml_source()
    csp_values = [urls["sso_url"], urls["slo_url"]]
    if additional_csp_values := ADDITIONAL_CSP_VALUES.get(type(config), []):
        csp_values.append(additional_csp_values)

    form_action_urls = " ".join(csp_values)
    CSPSetting.objects.set_for(config, [(CSPDirective.FORM_ACTION, form_action_urls)])
