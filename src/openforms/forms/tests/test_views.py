import tempfile
from io import BytesIO

from django.core.files import File
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

        self.assertTemplateUsed(list_page, "forms/form_list.html")

    def test_forbidden_no_main_website_configured(self):
        self.config.main_website = ""
        self.config.save()

        self.app.get(self.url, status=403)


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
            "of": {"layout": {"background": {"value": "#ffffff"}}}
        }
        self.config.save()

        form_page = self.app.get(self.url)

        style_node = form_page.pyquery("head > style")
        self.assertTrue(style_node)
        self.assertEqual(
            style_node.text(), ".openforms-theme { --of-layout-background: #ffffff; }"
        )

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_theme_stylesheets_included(self):
        """
        Assert that configured theme stylesheets are loaded in the correct order.
        """
        self.config.theme_stylesheet = "https://example.com/theme.css"
        self.config.theme_stylesheet_file = File(
            BytesIO(b".foo{display: block;}"), name="my-theme.css"
        )
        self.config.save()

        form_page = self.app.get(self.url)

        # look up the last two stylesheet links in the page
        stylesheet_links = [
            link for link in form_page.pyquery('link[rel="stylesheet"]')
        ][-2:]

        self.assertEqual(
            stylesheet_links[0].attrib["href"], "https://example.com/theme.css"
        )
        self.assertEqual(
            stylesheet_links[1].attrib["href"],
            self.config.theme_stylesheet_file.url,
        )

    def test_block_robots_indexing(self):
        self.config.allow_indexing_form_detail = False
        self.config.save()

        form_page = self.app.get(self.url)

        # see https://developers.google.com/search/docs/advanced/robots/robots_meta_tag#directives
        self.assertIn("X-Robots-Tag", form_page.headers)
        self.assertEqual(form_page.headers["X-Robots-Tag"], "noindex, nofollow")

        meta_tag = form_page.pyquery("meta[name='robots']")[0]
        self.assertEqual(meta_tag.attrib["content"], "noindex, nofollow")
