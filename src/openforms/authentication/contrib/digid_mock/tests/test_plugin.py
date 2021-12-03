from urllib.parse import quote

from django.test import RequestFactory, TestCase, override_settings

from openforms.forms.tests.factories import FormStepFactory

from ....constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from ....registry import register


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
class LoginTests(TestCase):
    def test_login(self):
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["digid-mock"],
            form_definition__login_required=True,
        )
        form = step.form
        plugin = register["digid-mock"]

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
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)
        self.assertRegex(response["Location"], r"^http://testserver/digid/")

        url = plugin.get_return_url(request, form)

        # bad without ?next=
        response = self.client.get(url + "?bsn=111222333")
        self.assertEqual(response.content, b"missing 'next' parameter")
        self.assertEqual(response.status_code, 400)

        # bad without ?bsn=
        response = self.client.get(f"{url}?next={next_url}")
        self.assertEqual(response.content, b"missing 'bsn' parameter")
        self.assertEqual(response.status_code, 400)

        # good
        response = self.client.get(url + "?next=http%3A%2F%2Ffoo.bar&bsn=111222333")
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
