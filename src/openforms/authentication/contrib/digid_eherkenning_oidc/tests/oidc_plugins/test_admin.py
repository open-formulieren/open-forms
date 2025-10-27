from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory


@disable_admin_mfa()
class AdminSmokeTests(WebTest):
    """
    Smoke tests to verify that the edit page in the admin loads without crashes.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = SuperUserFactory.create()

    def test_load_edit_page(self):
        clients = (
            OFOIDCClientFactory.create(with_digid=True),
            OFOIDCClientFactory.create(with_digid_machtigen=True),
            OFOIDCClientFactory.create(with_eherkenning=True),
            OFOIDCClientFactory.create(with_eherkenning_bewindvoering=True),
            OFOIDCClientFactory.create(with_eidas=True),
            OFOIDCClientFactory.create(with_eidas_company=True),
        )
        for client in clients:
            with self.subTest(identifier=client.identifier):
                url = reverse(
                    "admin:mozilla_django_oidc_db_oidcclient_change", args=(client.pk,)
                )

                change_page = self.app.get(url, user=self.user)

                self.assertEqual(change_page.status_code, 200)
