from django.contrib.auth.hashers import check_password as check_salted_hash
from django.http import HttpRequest

import structlog
from furl import furl
from rest_framework.request import Request
from rest_framework.reverse import reverse

from openforms.forms.models import Form
from openforms.submissions.models import Submission
from openforms.typing import AnyRequest

from .constants import (
    FORM_AUTH_SESSION_KEY,
    REGISTRATOR_SUBJECT_SESSION_KEY,
    AuthAttribute,
)
from .models import AuthInfo, RegistratorInfo
from .registry import register as auth_register
from .typing import BaseAuth, FormAuth

logger = structlog.stdlib.get_logger()


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
        submission=submission, defaults={**registrator_auth}
    )


def get_authentication_plugin(request: Request, form: Form) -> str:
    try:
        plugin = request.session[FORM_AUTH_SESSION_KEY]["plugin"]
        if not form.auth_backends.filter(backend=plugin).exists():
            raise ValueError(f"Unexpected plugin {plugin} used")

        return plugin
    except KeyError as exc:
        raise KeyError("Plugin cannot be retrieved from session") from exc


def is_authenticated_with_plugin(request: Request, expected_plugin: str) -> bool:
    try:
        return request.session[FORM_AUTH_SESSION_KEY]["plugin"] == expected_plugin
    except KeyError:
        return False


def is_authenticated_with_an_allowed_plugin(request: Request, form: Form) -> bool:
    try:
        get_authentication_plugin(request, form)
        return True
    except (ValueError, KeyError):
        return False


def meets_plugin_requirements(request: Request, form: Form, plugin_id: str) -> bool:
    # called after is_authenticated_with_plugin and get_authentication_plugin so this is
    # correct and there is a FormAuthenticationBackend object
    plugin = auth_register[plugin_id]
    authentication_backend = form.auth_backends.get(backend=plugin_id)

    if opts_serializer_cls := plugin.configuration_options:
        serializer = opts_serializer_cls(data=authentication_backend.options)
        # we can be brazen, as this code is called after succesful auth with the plugin
        serializer.is_valid(raise_exception=True)
        options = serializer.validated_data
    else:
        options = {}

    return plugin.check_requirements(request, options)


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


def check_user_is_submission_initiator(
    request: HttpRequest, submission: Submission
) -> bool:
    """
    Test if the logged in user matches the user who started the submission.

    The logged in user is not to be confused with a Django user, but the user stored in
    the session under ``FORM_AUTH_SESSION_KEY`` after logging in for a particular form.

    The session details are compared against ``submission.auth_info``. A match happens
    when the same auth plugin and identifier are present on both.

    Callers must verify that:

    Returns ``True`` if there's a match, and ``False`` otherwise.
    """
    if FORM_AUTH_SESSION_KEY not in request.session or not submission.is_authenticated:
        return False

    has_auth_attribute_match = (
        submission.auth_info.attribute
        == request.session[FORM_AUTH_SESSION_KEY]["attribute"]
    )

    submission_auth_value = submission.auth_info.value
    # there are two modus operandi - the submission may not be completed yet, in
    # which case we don't have a hashed value yet, but the raw value (used for
    # prefill and the like). There are also other flows where the attributes may
    # be hashed despite the submission not being completed yet.
    current_auth_value = request.session[FORM_AUTH_SESSION_KEY]["value"]

    if submission.auth_info.attribute_hashed:
        has_auth_value_match = check_salted_hash(
            current_auth_value, submission_auth_value, setter=None
        )
    else:
        # timing attacks are not a concern here, as you need to go through a valid
        # authentication flow first which sets the value in the session. Additionally,
        # enumeration would still be possible and you don't necessarily leak passwords
        # that may be used on other sites - end-users cannot change their BSN/KVK etc.
        # anyway.
        has_auth_value_match = submission_auth_value == current_auth_value

    return has_auth_attribute_match and has_auth_value_match


def remove_auth_info_from_session(request: AnyRequest) -> None:
    if FORM_AUTH_SESSION_KEY in request.session:
        del request.session[FORM_AUTH_SESSION_KEY]


def logout_submission(submission: Submission, request: AnyRequest) -> None:
    from openforms.submissions.utils import remove_submission_from_session

    remove_submission_from_session(submission, request.session)

    if submission.is_authenticated:
        if submission.auth_info.plugin in auth_register:
            plugin = auth_register[submission.auth_info.plugin]
            plugin.logout(request)

    if FORM_AUTH_SESSION_KEY in request.session:
        del request.session[FORM_AUTH_SESSION_KEY]

    if REGISTRATOR_SUBJECT_SESSION_KEY in request.session:
        del request.session[REGISTRATOR_SUBJECT_SESSION_KEY]
