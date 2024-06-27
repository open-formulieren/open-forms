from furl import furl
from rest_framework.request import Request
from rest_framework.reverse import reverse

from openforms.forms.models import Form
from openforms.submissions.models import Submission
from openforms.typing import AnyRequest

from .constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from .models import AuthInfo, RegistratorInfo
from .registry import register as auth_register
from .typing import BaseAuth, FormAuth


def store_auth_details(
    submission: Submission, form_auth: FormAuth, attribute_hashed: bool = False
) -> None:
    attribute = form_auth["attribute"]
    if attribute not in AuthAttribute.values:
        raise ValueError(f"Unexpected auth attribute {attribute} specified")

    AuthInfo.objects.update_or_create(
        submission=submission,
        defaults={**form_auth, "attribute_hashed": attribute_hashed},
    )


def store_registrator_details(
    submission: Submission, registrator_auth: BaseAuth
) -> None:
    attribute = registrator_auth["attribute"]
    if attribute not in AuthAttribute.values:
        raise ValueError(f"Unexpected auth attribute {attribute} specified")

    RegistratorInfo.objects.update_or_create(
        submission=submission, defaults=registrator_auth
    )


def is_authenticated_with_plugin(request: Request, expected_plugin: str) -> bool:
    try:
        return request.session[FORM_AUTH_SESSION_KEY]["plugin"] == expected_plugin
    except KeyError:
        return False


def is_authenticated_with_an_allowed_plugin(
    request: Request, allowed_plugins: list[str]
) -> bool:
    try:
        return request.session[FORM_AUTH_SESSION_KEY]["plugin"] in allowed_plugins
    except KeyError:
        return False


def meets_plugin_requirements(request: Request, config: dict) -> bool:
    # called after is_authenticated_with_plugin so this is correct
    plugin_id = request.session[FORM_AUTH_SESSION_KEY]["plugin"]
    plugin = auth_register[plugin_id]
    return plugin.check_requirements(request, config.get(plugin_id, {}))


def get_cosign_login_url(request: Request, form: Form, plugin_id: str) -> str:
    auth_url = reverse(
        "authentication:start",
        kwargs={
            "slug": form.slug,
            "plugin_id": plugin_id,
        },
        request=request,
    )
    next_url = reverse(
        "submissions:find-submission-for-cosign",
        kwargs={"form_slug": form.slug},
        request=request,
    )
    auth_page = furl(auth_url)
    auth_page.args.set("next", next_url)
    return auth_page.url


def remove_auth_info_from_session(request: AnyRequest) -> None:
    if FORM_AUTH_SESSION_KEY in request.session:
        del request.session[FORM_AUTH_SESSION_KEY]
