from datetime import timedelta

from django.conf import settings

from openforms.config.models import GlobalConfiguration

# for CORS, the session cookie must be set with SameSite "None" to be sent.
# This is a breaking change by Chrome, which was not going to be backported in Django
# 2.2.x. It's available from Django 3.1 onwards.
SAMESITE_VALUE = "None"


class SameSiteNoneCookieMiddlware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin")
        response = self.get_response(request)
        if settings.SESSION_COOKIE_NAME in response.cookies:
            # only set to None if we're in a cross-origin context (indicated by the Origin header)
            value = SAMESITE_VALUE if origin and not settings.DEBUG else "Lax"
            response.cookies[settings.SESSION_COOKIE_NAME]["samesite"] = value
        return response


class SessionTimeoutMiddleware:
    """
    Allows us to set the expiry time of the session based on what
    is configured in our GlobalConfiguration
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        config = GlobalConfiguration.get_solo()
        timeout = (
            config.admin_session_timeout
            if request.user.is_staff
            else config.form_session_timeout
        )
        # https://docs.djangoproject.com/en/2.2/topics/http/sessions/#django.contrib.sessions.backends.base.SessionBase.set_expiry
        # request.session.set_expiry(timedelta(minutes=timeout).seconds)
        request.session.set_expiry(10)
        return self.get_response(request)
