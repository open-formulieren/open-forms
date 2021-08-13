from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory

from .factories import DomainFactory


class MultiDomainAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.superuser = SuperUserFactory.create()
        cls.url = reverse("admin:index")

    def test_no_domains_switcher(self):
        response = self.app.get(self.url, user=self.superuser)
        self.assertNotIn("user-tools__switcher", response.text)

    def test_single_domain_switcher(self):
        DomainFactory.create()

        response = self.app.get(self.url, user=self.superuser)
        self.assertNotIn("user-tools__switcher", response.text)

    def test_multi_domains_switcher(self):
        DomainFactory.create_batch(2)

        response = self.app.get(self.url, user=self.superuser)
        self.assertIn("user-tools__switcher", response.text)

    def test_multi_domains_switcher_current_selected(self):
        DomainFactory.create()
        current_domain = DomainFactory.create(is_current=True)

        response = self.app.get(self.url, user=self.superuser)
        self.assertIn("user-tools__switcher", response.text)

        self.assertEqual(
            response.pyquery(".user-tools__switcher option:selected").text(),
            current_domain.name,
        )
