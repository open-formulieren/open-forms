from urllib.parse import quote

from django.test import RequestFactory, TestCase, override_settings

from openforms.forms.tests.factories import FormStepFactory

from ....constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from ....registry import register


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
class LoginTests(TestCase):
    def test_login_bsn_and_baseclass(self):
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["demo"],
            form_definition__login_required=True,
        )
        form = step.form
        plugin = register["demo"]

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        url = plugin.get_start_url(request, form)
        next_url = quote("http://foo.bar")

        # bad without ?next=
        response = self.client.get(url)
        self.assertEqual(response.content, b"missing 'next' parameter")
        self.assertEqual(response.status_code, 400)

        # good
        response = self.client.get(f"{url}?next={next_url}")
        self.assertRegex(response["content-type"], r"^text/html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

        url = plugin.get_return_url(request, form)

        # bad without next
        response = self.client.post(url, data={"bsn": "111222333"})
        self.assertRegex(response["content-type"], r"^text/html")
        self.assertEqual(response.content, b"invalid data")
        self.assertEqual(response.status_code, 400)

        # bad without bsn
        response = self.client.post(url, data={"next": "http://foo.bar"})
        self.assertRegex(response["content-type"], r"^text/html")
        self.assertEqual(response.content, b"invalid data")
        self.assertEqual(response.status_code, 400)

        # bad get
        response = self.client.get(url, data={"next": "http://foo.bar"})
        self.assertEqual(response.status_code, 405)

        # good
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)

        response = self.client.post(
            url, data={"next": "http://foo.bar", "bsn": "111222333"}
        )
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://foo.bar")

        self.assertIn(FORM_AUTH_SESSION_KEY, self.client.session)
        self.assertEqual(
            AuthAttribute.bsn, self.client.session[FORM_AUTH_SESSION_KEY]["attribute"]
        )
        self.assertEqual(
            "111222333", self.client.session[FORM_AUTH_SESSION_KEY]["value"]
        )

    def test_login_kvk(self):
        # simplified from above just checking the kvk plugin
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["demo-kvk"],
            form_definition__login_required=True,
        )
        form = step.form
        plugin = register["demo-kvk"]

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        url = plugin.get_start_url(request, form)
        next_url = quote("http://foo.bar")

        # start
        response = self.client.get(f"{url}?next={next_url}")
        self.assertRegex(response["content-type"], r"^text/html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

        # return
        url = plugin.get_return_url(request, form)

        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)

        response = self.client.post(
            url, data={"next": "http://foo.bar", "kvk": "111222333"}
        )
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://foo.bar")

        self.assertIn(FORM_AUTH_SESSION_KEY, self.client.session)
        self.assertEqual("kvk", self.client.session[FORM_AUTH_SESSION_KEY]["attribute"])
        self.assertEqual(
            "111222333", self.client.session[FORM_AUTH_SESSION_KEY]["value"]
        )
