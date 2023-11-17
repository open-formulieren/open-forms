import json
from typing import Any

from django.http.response import HttpResponse
from django.test import SimpleTestCase

from furl import furl

from .frontend import SDKAction


class FrontendRedirectMixin:
    """A mixin providing a helper method checking frontend redirects."""

    def assertRedirectsToFrontend(
        self: SimpleTestCase,
        response: HttpResponse,
        frontend_base_url: str,
        action: SDKAction,
        action_params: dict[str, str] | None = None,
        **kwargs: Any
    ) -> None:
        """Assert that a response redirected to a specific frontend URL.

        :param response: The response to test the redirection on.
        :param frontend_base_url: The base URL of the frontend.
        :param action: The SDK action performed.
        :param action_params: Optional parameters for the action.
        :param `**kwargs`: Additional kwargs to be passed to :meth:`django.test.SimpleTestCase.assertRedirects`.
        """

        expected_redirect_url = furl(frontend_base_url)
        expected_redirect_url.remove("_of_action")
        expected_redirect_url.remove("_of_action_params")
        expected_redirect_url.add(
            {
                "_of_action": action,
            }
        )

        if action_params:
            expected_redirect_url.add({"_of_action_params": json.dumps(action_params)})

        return self.assertRedirects(
            response,
            expected_redirect_url.url,
            **kwargs,
        )
