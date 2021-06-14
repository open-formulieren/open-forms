from dataclasses import dataclass
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from openforms.forms.models import Form


@dataclass()
class LoginLogo:
    title: str
    image_src: str
    href: str = ""


@dataclass()
class LoginInfo:
    identifier: str
    label: str
    logo: LoginLogo = None
    url: Optional[str] = None


class BasePlugin:
    verbose_name = _("Set the 'verbose_name' attribute for a human-readable name")
    """
    Specify the human-readable label for the plugin.
    """
    return_method = "GET"

    def __init__(self, identifier: str):
        self.identifier = identifier

    # override

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str
    ) -> HttpResponse:
        # redirect/go to auth service (like digid)
        raise NotImplementedError()

    def handle_return(self, request: HttpRequest, form: Form) -> HttpResponse:
        # process and validate return information, store bsn in session
        raise NotImplementedError()

    # helpers

    def get_start_url(self, request: HttpRequest, form: Form) -> str:
        return reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
        )

    def get_return_url(self, request: HttpRequest, form: Form) -> str:
        return reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
        )

    def get_login_info(self, request: HttpRequest, form: Form) -> LoginInfo:
        info = LoginInfo(
            self.identifier,
            self.get_label(),
            url=self.get_start_url(request, form),
            logo=self.get_logo(request),
        )
        return info

    # cosmetics

    def get_label(self) -> str:
        return self.verbose_name

    def get_logo(self, request: HttpRequest) -> Optional[LoginLogo]:
        return None
