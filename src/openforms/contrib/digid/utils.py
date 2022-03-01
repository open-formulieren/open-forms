from typing import Optional

from django.templatetags.static import static

from openforms.authentication.base import LoginLogo


def get_digid_logo(request, label) -> Optional[LoginLogo]:
    return LoginLogo(
        title=label,
        image_src=request.build_absolute_uri(static("img/digid-46x46.png")),
        href="https://www.digid.nl/",
    )
