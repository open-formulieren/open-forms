from django.test import RequestFactory, TestCase

from openforms.authentication.registry import register
from openforms.forms.tests.factories import FormStepFactory


class LoginTests(TestCase):
    def test_login(self):
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["demo"],
            form_definition__login_required=True,
        )
        form = step.form
        plugin = register["demo"]

        factory = RequestFactory()
        request = factory.get("/mypage")

        url = plugin.get_start_url(request, form)

        # bad without ?next=
        response = self.client.get(url)
        self.assertEqual(response.content, b"missing 'next' parameter")
        self.assertEqual(response.status_code, 400)

        # good
        response = self.client.get(url + "?next=http%3A%2F%2Ffoo.bar")
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

        self.assertNotIn("bsn", self.client.session)

        # good
        response = self.client.post(
            url, data={"next": "http://foo.bar", "bsn": "111222333"}
        )
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://foo.bar")

        self.assertIn("bsn", self.client.session)
        self.assertIn(self.client.session["bsn"], "111222333")
