from typing import Optional

from django.templatetags.static import static

from openforms.authentication.base import LoginLogo


def get_eherkenning_logo(request, label) -> Optional[LoginLogo]:
    return LoginLogo(
        title=label,
        image_src=request.build_absolute_uri(static("img/eherkenning.png")),
        href="https://www.eherkenning.nl/",
    )
