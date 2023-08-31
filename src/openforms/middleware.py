from datetime import timedelta

from django.http import HttpRequest
from django.middleware.csrf import get_token

from openforms.config.models import GlobalConfiguration
from openforms.typing import RequestHandler

SESSION_EXPIRES_IN_HEADER = "X-Session-Expires-In"
CSRF_TOKEN_HEADER_NAME = "X-CSRFToken"
IS_FORM_DESIGNER_HEADER_NAME = "X-Is-Form-Designer"


class SessionTimeoutMiddleware:
    """
    Allows us to set the expiry time of the session based on what
    is configured in our GlobalConfiguration
    """

    def __init__(self, get_response: RequestHandler):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        config = GlobalConfiguration.get_solo()
        timeout = (
            config.admin_session_timeout
            if request.user.is_staff
            else config.form_session_timeout
        )
        # https://docs.djangoproject.com/en/2.2/topics/http/sessions/#django.contrib.sessions.backends.base.SessionBase.set_expiry
        expires_in = int(timedelta(minutes=timeout).total_seconds())
        request.session.set_expiry(expires_in)
        response = self.get_response(request)
        response[SESSION_EXPIRES_IN_HEADER] = expires_in
        return response


class CsrfTokenMiddleware:
    """
    Add a CSRF Token to a response header
    """

    def __init__(self, get_response: RequestHandler):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)

        # Only add the CSRF token header if it's an api endpoint
        if not request.path_info.startswith("/api"):
            return response

        response[CSRF_TOKEN_HEADER_NAME] = get_token(request)
        return response


class CanNavigateBetweenStepsMiddleware:
    """
    Add a header to the response to let the frontend know if the user is allowed to navigate between submission steps
    that have not been completed yet.
    """

    def __init__(self, get_response: RequestHandler):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)

        # Only add the header if it's an api endpoint
        if not request.path_info.startswith("/api"):
            return response

        user = request.user

        if user.is_authenticated:
            response[IS_FORM_DESIGNER_HEADER_NAME] = "false"

        if user.is_staff and user.has_perm("forms.change_form"):
            response[IS_FORM_DESIGNER_HEADER_NAME] = "true"

        return response
