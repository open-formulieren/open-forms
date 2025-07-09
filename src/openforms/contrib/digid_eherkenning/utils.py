from django.templatetags.static import static

from openforms.authentication.constants import LogoAppearance


def get_digid_logo(request) -> dict[str, str]:
    return {
        "image_src": request.build_absolute_uri(static("img/digid-46x46.png")),
        "href": "https://www.digid.nl/",
        "appearance": LogoAppearance.dark,
    }


def get_eherkenning_logo(request) -> dict[str, str]:
    return {
        "image_src": request.build_absolute_uri(static("img/eherkenning.png")),
        "href": "https://www.eherkenning.nl/",
        "appearance": LogoAppearance.light,
    }


def get_eidas_logo(request) -> dict[str, str]:
    return {
        "image_src": request.build_absolute_uri(static("img/eidas.png")),
        "href": "https://digital-strategy.ec.europa.eu/en/policies/eu-trust-mark",
        "appearance": LogoAppearance.light,
    }
