from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, TypedDict

from django.http import HttpRequest, HttpResponse

from furl import furl
from rest_framework.request import Request
from rest_framework.reverse import reverse

from openforms.authentication.models import AuthInfo
from openforms.authentication.types import (
    DigiDContext,
    DigiDMachtigenContext,
    EHerkenningContext,
    EHerkenningMachtigenContext,
    EmployeeContext,
    YiviContext,
)
from openforms.forms.models import Form
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.typing import AnyRequest, JSONObject, StrOrPromise

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


class CosignSlice(TypedDict):
    identifier: str
    fields: JSONObject


class Options(TypedDict):
    pass


class BasePlugin[OptionsT: Options](AbstractBasePlugin):
    provides_auth: ClassVar[Sequence[AuthAttribute]]
    return_method = "GET"
    is_for_gemachtigde = False

    # Indicating if the plugin handles the authInfo -> authContext themselves.
    # Works in conjunction with ``BasePlugin.auth_info_to_auth_context``
    manage_auth_context: bool = False

    # override

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str, options: OptionsT
    ) -> HttpResponse:
        # redirect/go to auth service (like digid)
        raise NotImplementedError()  # noqa

    def handle_return(
        self, request: Request, form: Form, options: OptionsT
    ) -> HttpResponse:
        # process and validate return information, store bsn in session
        raise NotImplementedError()  # noqa

    def handle_co_sign(self, request: Request, form: Form) -> CosignSlice:
        """
        Process the authentication and return a dict of co-sign details.

        The co-sign details are stored on ``Submission.co_sign_data`` and must match the
        schema (except for the ``plugin`` key).
        """
        raise NotImplementedError()  # noqa

    # helpers

    def auth_info_to_auth_context(
        self, auth_info: AuthInfo
    ) -> (
        DigiDContext
        | DigiDMachtigenContext
        | EHerkenningContext
        | EHerkenningMachtigenContext
        | EmployeeContext
        | YiviContext
    ):
        """
        Plugin custom auth info to auth context handling.

        This will be executed during the AuthInfo ``to_auth_context_data`` when
        ``manage_auth_context`` is set to ``True``.
        """
        raise NotImplementedError(
            "Subclasses must implement 'auth_info_to_auth_context'"
        )

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

    def check_requirements(self, request: AnyRequest, options: OptionsT) -> bool:
        "Check if the request meets requirements"
        return True

    # cosmetics

    def get_label(self) -> StrOrPromise:
        return self.verbose_name

    def get_logo(self, request: HttpRequest) -> LoginLogo | None:
        return None
