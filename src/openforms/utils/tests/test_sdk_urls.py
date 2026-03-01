from django.test import TestCase, override_settings

from unittest_parametrize import ParametrizedTestCase, param, parametrize

from ..sdk_static import get_sdk_urls


class StableSDKUrlTests(ParametrizedTestCase, TestCase):
    """
    Ensure that stable SDK URLs can be used, independent of which version is deployed.

    uwsgi --static-map serves the file IF it's available in the path, so when using
    sdk version latest, the /static/sdk/open-forms-sdk.(js|css) URLs will resolve and
    be served by uwsgi. If there's no match, then the request is handled by the app,
    which emits a 302 redirect to the correct asset location.
    """

    def setUp(self):
        super().setUp()

        get_sdk_urls.cache_clear()
        self.addCleanup(get_sdk_urls.cache_clear)

    @parametrize(
        ("stable_url", "resolved_url"),
        [
            param(
                "/static/sdk/open-forms-sdk.js",
                "/static/sdk/1.2.3/bundles/open-forms-sdk.js",
                id="umd",
            ),
            param(
                "/static/sdk/open-forms-sdk.mjs",
                "/static/sdk/1.2.3/bundles/open-forms-sdk.mjs",
                id="esm",
            ),
            param(
                "/static/sdk/open-forms-sdk.css",
                "/static/sdk/1.2.3/bundles/open-forms-sdk.css",
                id="css",
            ),
        ],
    )
    @override_settings(SDK_RELEASE="1.2.3")
    def test_sdk_latest(self, stable_url: str, resolved_url: str):
        response = self.client.get(stable_url)

        self.assertRedirects(response, resolved_url, fetch_redirect_response=False)

    def test_invalid_extension(self):
        response = self.client.get("/static/sdk/open-forms-sdk.svg")

        self.assertEqual(response.status_code, 400)
