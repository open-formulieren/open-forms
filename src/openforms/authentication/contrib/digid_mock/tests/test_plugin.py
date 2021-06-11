from django.test import RequestFactory, TestCase

from openforms.authentication.registry import register
from openforms.forms.tests.factories import FormStepFactory


class LoginTests(TestCase):
    def test_login(self):
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["digid-mock"],
            form_definition__login_required=True,
        )
        form = step.form
        plugin = register["digid-mock"]

        factory = RequestFactory()
        request = factory.get("/mypage")

        url = plugin.get_start_url(request, form)

        # bad without ?next=
        response = self.client.get(url)
        self.assertEqual(response.content, b"missing 'next' parameter")
        self.assertEqual(response.status_code, 400)

        # good
        response = self.client.get(url + "?next=http%3A%2F%2Ffoo.bar")
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)
        self.assertRegex(response["Location"], r"^http://testserver/digid/")

        url = plugin.get_return_url(request, form)

        # bad without ?next=
        response = self.client.get(url + "?bsn=111222333")
        self.assertEqual(response.content, b"missing 'next' parameter")
        self.assertEqual(response.status_code, 400)

        # bad without ?bsn=
        response = self.client.get(url + "?next=http%3A%2F%2Ffoo.bar")
        self.assertEqual(response.content, b"missing 'bsn' parameter")
        self.assertEqual(response.status_code, 400)

        # good
        response = self.client.get(url + "?next=http%3A%2F%2Ffoo.bar&bsn=111222333")
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://foo.bar")

        self.assertIn("bsn", self.client.session)
        self.assertIn(self.client.session["bsn"], "111222333")
