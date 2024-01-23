from dataclasses import dataclass
from typing import Any, Optional, TypedDict

from django.db.models import TextChoices
from django.http import HttpRequest, HttpResponse

from furl import furl
from rest_framework.reverse import reverse

from openforms.forms.models import Form
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.typing import AnyRequest

from .constants import AuthAttribute


@dataclass()
class LoginLogo:
    title: str
    image_src: str
    appearance: str
    href: str = ""


@dataclass()
class LoginInfo:
    identifier: str
    label: str
    logo: LoginLogo | None = None
    url: Optional[str] = None
    is_for_gemachtigde: bool = False


class Choice(TypedDict):
    value: str | int
    label: str


class BasePlugin(AbstractBasePlugin):
    provides_auth: AuthAttribute
    assurance_levels: type[TextChoices] = TextChoices
    return_method = "GET"
    is_for_gemachtigde = False

    # override

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str
    ) -> HttpResponse:
        # redirect/go to auth service (like digid)
        raise NotImplementedError()  # noqa

    def handle_return(self, request: HttpRequest, form: Form) -> HttpResponse:
        # process and validate return information, store bsn in session
        raise NotImplementedError()  # noqa

    def handle_co_sign(self, request: HttpRequest, form: Form) -> dict[str, Any]:
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

    def get_registrator_subject_url(
        self, request: HttpRequest, form: Form, form_url: str
    ) -> str:
        f = furl(
            reverse(
                "authentication:registrator-subject",
                kwargs={"slug": form.slug},
                request=request,
            )
        )
        f.args["next"] = form_url
        return f.url

    def logout(self, request: HttpRequest):
        """
        Can be overridden to implement custom logout behaviour
        """
        pass

    def get_login_info(self, request: HttpRequest, form: Form | None) -> LoginInfo:
        info = LoginInfo(
            self.identifier,
            self.get_label(),
            url=self.get_start_url(request, form) if form else "",
            logo=self.get_logo(request),
            is_for_gemachtigde=self.is_for_gemachtigde,
        )
        return info

    def get_assurance_levels(self) -> list[Choice]:
        return [
            Choice(value=loa.value, label=loa.label) for loa in self.assurance_levels
        ]

    def check_requirements(self, request: AnyRequest, config: dict) -> bool:
        "Check if the request meets requirements"
        return True

    # cosmetics

    def get_label(self) -> str:
        return self.verbose_name

    def get_logo(self, request: HttpRequest) -> Optional[LoginLogo]:
        return None
