from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.http import HttpRequest, HttpResponse

from rest_framework.reverse import reverse

from openforms.forms.models import Form
from openforms.plugins.plugin import AbstractBasePlugin


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


class BasePlugin(AbstractBasePlugin):
    provides_auth = None
    return_method = "GET"

    # override

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str
    ) -> HttpResponse:
        # redirect/go to auth service (like digid)
        raise NotImplementedError()  # noqa

    def handle_return(self, request: HttpRequest, form: Form) -> HttpResponse:
        # process and validate return information, store bsn in session
        raise NotImplementedError()  # noqa

    def handle_co_sign(self, request: HttpRequest, form: Form) -> Dict[str, Any]:
        """
        Process the authentication and return a dict of co-sign details.

        The co-sign details are stored on ``Submission.co_sign_data`` and must match the
        schema (except for the ``plugin`` key).
        """
        raise NotImplementedError()  # noqa

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

    def get_provides_auth(self) -> List[str]:
        if not self.provides_auth:
            return []
        elif isinstance(self.provides_auth, str):
            return [self.provides_auth]
        else:
            return list(self.provides_auth)

    # cosmetics

    def get_label(self) -> str:
        return self.verbose_name

    def get_logo(self, request: HttpRequest) -> Optional[LoginLogo]:
        return None
