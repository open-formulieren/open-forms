from django.test import TestCase, override_settings


class StableSDKUrlTests(TestCase):
    """
    Ensure that stable SDK URLs can be used, independent of which version is deployed.

    uwsgi --static-map serves the file IF it's available in the path, so when using
    sdk version latest, the /static/sdk/open-forms-sdk.(js|css) URLs will resolve and
    be served by uwsgi. If there's no match, then the request is handled by the app,
    which emits a 302 redirect to the correct asset location.
    """

    @override_settings(SDK_RELEASE="1.2.3")
    def test_sdk_latest(self):
        base = "/static/sdk/"

        js_url = f"{base}open-forms-sdk.js"
        with self.subTest(js_url=js_url):
            js_response = self.client.get(js_url)

            self.assertRedirects(
                js_response,
                f"{base}1.2.3/bundles/open-forms-sdk.js",
                fetch_redirect_response=False,
            )

        mjs_url = f"{base}open-forms-sdk.mjs"
        with self.subTest(js_url=mjs_url):
            js_response = self.client.get(mjs_url)

            self.assertRedirects(
                js_response,
                f"{base}1.2.3/bundles/open-forms-sdk.mjs",
                fetch_redirect_response=False,
            )

        css_url = f"{base}open-forms-sdk.css"
        with self.subTest(css_url=css_url):
            css_response = self.client.get(css_url)

            self.assertRedirects(
                css_response,
                f"{base}1.2.3/bundles/open-forms-sdk.css",
                fetch_redirect_response=False,
            )

    def test_invalid_extension(self):
        response = self.client.get("/static/sdk/open-forms-sdk.svg")

        self.assertEqual(response.status_code, 400)
