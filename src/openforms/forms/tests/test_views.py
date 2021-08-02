from django.test import override_settings
from django.urls import reverse, reverse_lazy

from django_webtest import WebTest

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.config.models import GlobalConfiguration
from openforms.tests.utils import NOOP_CACHES

from .factories import FormFactory


@override_settings(
    CACHES=NOOP_CACHES, SESSION_ENGINE="django.contrib.sessions.backends.db"
)
class FormListViewTests(WebTest):

    url = reverse_lazy("forms:form-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = GlobalConfiguration.get_solo()
        config.main_website = "https://example.com"
        config.save()

        cls.config = config

    def test_redirect_anon_user(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response, "https://example.com", fetch_redirect_response=False
        )

    def test_redirect_non_staff_user(self):
        user = UserFactory.create()

        list_page = self.app.get(self.url, user=user)

        self.assertEqual(list_page.status_code, 302)

    def test_show_list_logged_in_staff(self):
        user = StaffUserFactory.create()

        list_page = self.app.get(self.url, user=user)

        self.assertTemplateUsed(list_page, "core/views/form/form_list.html")

    def test_show_list_no_main_website_configured(self):
        self.config.main_website = ""
        self.config.save()

        list_page = self.app.get(self.url)

        self.assertTemplateUsed(list_page, "core/views/form/form_list.html")


@override_settings(
    CACHES=NOOP_CACHES, SESSION_ENGINE="django.contrib.sessions.backends.db"
)
class FormDetailViewTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = GlobalConfiguration.get_solo()
        config.main_website = "https://example.com"
        config.save()

        cls.config = config

        form = FormFactory.create()
        cls.url = reverse("forms:form-detail", kwargs={"slug": form.slug})

    def test_detail_page_renders_sdk_snippet(self):
        form_page = self.app.get(self.url)

        self.assertTemplateUsed(form_page, "forms/sdk_snippet.html")

    def test_design_tokens_rendered(self):
        self.config.design_token_values = {
            "layout": {"background": {"value": "#ffffff"}}
        }
        self.config.save()

        form_page = self.app.get(self.url)

        style_node = form_page.pyquery("head > style")
        self.assertTrue(style_node)
        self.assertEqual(
            style_node.text(), ":root { --of-layout-background: #ffffff; }"
        )
