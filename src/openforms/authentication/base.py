from dataclasses import dataclass
from typing import Any, Generic, TypedDict, TypeVar

from django.db.models import TextChoices
from django.http import HttpRequest, HttpResponse

from furl import furl
from rest_framework.request import Request
from rest_framework.reverse import reverse

from openforms.forms.models import Form
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.typing import AnyRequest, StrOrPromise

from .constants import AuthAttribute
from .utils import get_cosign_login_url


@dataclass()
class LoginLogo:
    title: str
    image_src: str
    appearance: str
    href: str = ""


@dataclass()
class LoginInfo:
    identifier: str
    label: StrOrPromise
    logo: LoginLogo | None = None
    url: str | None = None
    is_for_gemachtigde: bool = False


class Choice(TypedDict):
    value: str | int
    label: str


class Options(TypedDict):
    pass


OptionsT = TypeVar("OptionsT", bound=Options)


class BasePlugin(Generic[OptionsT], AbstractBasePlugin):
    provides_auth: AuthAttribute
    supports_loa_override = False
    assurance_levels: type[TextChoices] = TextChoices
    return_method = "GET"
    is_for_gemachtigde = False

    # override

    def start_login(
        self, request: Request, form: Form, form_url: str, options: OptionsT
    ) -> HttpResponse:
        # redirect/go to auth service (like digid)
        raise NotImplementedError()  # noqa

    def handle_return(
        self, request: Request, form: Form, options: OptionsT
    ) -> HttpResponse:
        # process and validate return information, store bsn in session
        raise NotImplementedError()  # noqa

    def handle_co_sign(self, request: Request, form: Form) -> dict[str, Any]:
        """
        Process the authentication and return a dict of co-sign details.

        The co-sign details are stored on ``Submission.co_sign_data`` and must match the
        schema (except for the ``plugin`` key).
        """
        raise NotImplementedError()  # noqa

    # helpers

    def get_start_url(self, request: Request, form: Form) -> str:
        return reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
        )

    def get_return_url(self, request: Request, form: Form) -> str:
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

    def get_login_info(
        self, request: Request, form: Form | None, is_for_cosign: bool = False
    ) -> LoginInfo:
        if is_for_cosign:
            login_url = (
                get_cosign_login_url(request, form, self.identifier) if form else ""
            )
        else:
            login_url = self.get_start_url(request, form) if form else ""

        info = LoginInfo(
            self.identifier,
            self.get_label(),
            url=login_url,
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

    def get_label(self) -> StrOrPromise:
        return self.verbose_name

    def get_logo(self, request: HttpRequest) -> LoginLogo | None:
        return None
