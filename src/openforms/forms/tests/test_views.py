import tempfile
from io import BytesIO

from django.core.files import File
from django.test import override_settings
from django.urls import reverse, reverse_lazy

from django_webtest import WebTest

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.config.models import GlobalConfiguration
from openforms.config.tests.factories import ThemeFactory
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

        cls.config: GlobalConfiguration = config

        form = FormFactory.create()
        cls.form = form
        cls.url = reverse("forms:form-detail", kwargs={"slug": form.slug})

    def test_detail_page_renders_sdk_snippet(self):
        form_page = self.app.get(self.url)

        self.assertTemplateUsed(form_page, "forms/sdk_snippet.html")

    def test_design_tokens_rendered(self):
        theme = ThemeFactory.create(
            design_token_values={"of": {"layout": {"background": {"value": "#ffffff"}}}}
        )
        self.config.default_theme = theme
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
        theme = ThemeFactory.create(
            stylesheet="https://example.com/theme.css",
            stylesheet_file=File(
                BytesIO(b".foo{display: block;}"), name="my-theme.css"
            ),
        )
        self.config.default_theme = theme
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
            theme.stylesheet_file.url,
        )

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_form_specific_theme_used(self):
        theme = ThemeFactory.create(
            stylesheet="https://example.com/theme.css",
            stylesheet_file=File(
                BytesIO(b".foo{display: block;}"), name="my-theme.css"
            ),
        )
        self.config.default_theme = theme
        self.config.save()

        theme2 = ThemeFactory.create(stylesheet="https://example.com/override.css")
        self.form.theme = theme2
        self.form.save()

        form_page = self.app.get(self.url)

        # look up the last two stylesheet links in the page
        stylesheet_links = {
            link.attrib["href"] for link in form_page.pyquery('link[rel="stylesheet"]')
        }

        # only the override theme styles may be applied, not the global default
        self.assertIn("https://example.com/override.css", stylesheet_links)
        self.assertNotIn("https://example.com/theme.css", stylesheet_links)
        self.assertNotIn(theme.stylesheet_file.url, stylesheet_links)

    def test_block_robots_indexing(self):
        self.config.allow_indexing_form_detail = False
        self.config.save()

        form_page = self.app.get(self.url)

        # see https://developers.google.com/search/docs/advanced/robots/robots_meta_tag#directives
        self.assertIn("X-Robots-Tag", form_page.headers)
        self.assertEqual(form_page.headers["X-Robots-Tag"], "noindex, nofollow")

        meta_tag = form_page.pyquery("meta[name='robots']")[0]
        self.assertEqual(meta_tag.attrib["content"], "noindex, nofollow")


@override_settings(
    CACHES=NOOP_CACHES, SESSION_ENGINE="django.contrib.sessions.backends.db"
)
class ThemePreviewViewTests(WebTest):
    def test_must_be_staff_user(self):
        theme = ThemeFactory.create()
        form = FormFactory.create(generate_minimal_setup=True)
        user = UserFactory.create(is_staff=False)
        url = reverse(
            "forms:theme-preview",
            kwargs={"theme_pk": theme.pk, "slug": form.slug},
        )

        response = self.app.get(url, user=user, status=403)

        self.assertEqual(response.status_code, 403)

    def test_404_on_nonexistent_theme(self):
        form = FormFactory.create(generate_minimal_setup=True)
        user = UserFactory.create(is_staff=True)
        url = reverse(
            "forms:theme-preview",
            kwargs={"theme_pk": 42, "slug": form.slug},
        )

        response = self.app.get(url, user=user, status=404)

        self.assertEqual(response.status_code, 404)

    def test_renders_with_sufficient_permissions_and_existing_objects(self):
        theme = ThemeFactory.create()
        form = FormFactory.create(generate_minimal_setup=True)
        user = UserFactory.create(is_staff=True)
        url = reverse(
            "forms:theme-preview",
            kwargs={"theme_pk": theme.pk, "slug": form.slug},
        )

        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)
