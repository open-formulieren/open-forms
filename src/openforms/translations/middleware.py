from django.conf import settings
from django.http import HttpRequest
from django.utils import translation

import structlog

from openforms.typing import RequestHandler
from openforms.utils.urls import is_admin_request

logger = structlog.stdlib.get_logger(__name__)


def _remove_language_cookie_from_request(request: HttpRequest) -> None:
    """
    Produce a request instance without cookie-based language information.

    settings.LANGUAGE_COOKIE_NAME
    """
    cookie_name = settings.LANGUAGE_COOKIE_NAME
    cookie_present = cookie_name in request.COOKIES
    if cookie_present:
        del request.COOKIES[cookie_name]
    logger.debug("language_cookie_removal", was_present=cookie_present)


class AdminLocaleMiddleware:
    """
    Discard the language cookie for locale-information.

    While the language cookie is the primary mechanism to specify the desired language,
    this applies to the public UI and not the admin. For the admin UI, we either use
    the browser Accept-Language header or look up user preferences stored in the user
    account itself.
    """

    def __init__(self, get_response: RequestHandler):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        # we do not language-code prefixed URLs
        if is_admin_request(request):
            _remove_language_cookie_from_request(request)
            language = ""
            if request.user.is_authenticated:
                language = request.user.ui_language
            if not language:
                language = translation.get_language_from_request(
                    request, check_path=False
                )
            translation.activate(language)
        response = self.get_response(request)
        return response
