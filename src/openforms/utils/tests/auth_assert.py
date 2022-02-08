from django.conf import settings
from django.shortcuts import resolve_url

from furl import furl


class AuthAssertMixin:
    def assertLoginRequired(self, response, redirect_to: str, **kwargs):
        expected_url = furl(resolve_url(settings.LOGIN_URL))
        expected_url.args["next"] = redirect_to
        self.assertRedirects(response, expected_url, **kwargs)
