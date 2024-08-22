from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory

from .factories import EmailVerificationFactory


@disable_admin_mfa()
class EmailVerificationAdminTests(WebTest):

    def test_search_fields(self):
        # smoke test that the search fields are correctly configured
        user = SuperUserFactory.create()
        url = reverse("admin:submissions_emailverification_changelist")
        EmailVerificationFactory.create_batch(3)
        EmailVerificationFactory.create(verified=True, email="openforms@opengem.nl")

        response = self.app.get(url, {"q": "opengem.nl"}, user=user)

        self.assertEqual(response.status_code, 200)
        result_rows = response.pyquery("#result_list > tbody > tr")
        self.assertEqual(len(result_rows), 1)
