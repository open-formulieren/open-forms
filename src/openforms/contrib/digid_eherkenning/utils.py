from typing import Dict

from django.templatetags.static import static


def get_digid_logo(request) -> Dict[str, str]:
    return {
        "image_src": request.build_absolute_uri(static("img/digid-46x46.png")),
        "href": "https://www.digid.nl/",
    }


def get_eherkenning_logo(request) -> Dict[str, str]:
    return {
        "image_src": request.build_absolute_uri(static("img/eherkenning.png")),
        "href": "https://www.eherkenning.nl/",
    }
