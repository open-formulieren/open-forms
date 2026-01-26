import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from webtest import Upload

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.tests.factories import FormFactory

from .factories import ThemeFactory

LOGO_FILE = Path(settings.BASE_DIR) / "docs" / "logo.svg"


@disable_admin_mfa()
@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = SuperUserFactory.create()

    def setUp(self):
        super().setUp()

        self.app.set_user(self.user)

        def _cleanup():
            try:
                shutil.rmtree(settings.MEDIA_ROOT)
            except Exception:
                pass

        self.addCleanup(_cleanup)

    def test_upload_svg(self):
        with self.subTest(part="admin config"):
            theme = ThemeFactory.create()
            url = reverse("admin:config_theme_change", args=(theme.pk,))

            change_page = self.app.get(url)

            with open(LOGO_FILE, "rb") as infile:
                upload = Upload("logo.svg", infile.read(), "image/svg+xml")

            form = change_page.forms["theme_form"]
            form["logo"] = upload
            response = form.submit()

            self.assertEqual(response.status_code, 302)
            theme.refresh_from_db()
            self.assertEqual(theme.logo, "logo/logo.svg")

        with self.subTest(part="logo used"):
            form = FormFactory.create(theme=theme)
            url = reverse("forms:form-detail", kwargs={"slug": form.slug})

            form_page = self.app.get(url)

            header = form_page.pyquery(".utrecht-page-header")
            self.assertTrue(header)
            self.assertIn(
                "utrecht-page-header--openforms-with-logo", header.attr("class")
            )

            style_tag = form_page.pyquery("style")
            self.assertIn(
                f"--of-header-logo-url: url('{theme.logo.url}')",
                style_tag.text(),
            )

    def test_upload_malicious_svg(self):
        bad_svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="25" fill="green" onclick="alert('forget about me?')" />
            <script>//<![CDATA[
                alert("I am malicious >:)")
            //]]></script>
            <g>
                <rect class="btn" x="0" y="0" width="10" height="10" fill="red" onload="alert('click!')" />
            </g>
        </svg>
        """
        sanitized_svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="25" fill="green"></circle>
            <g>
                <rect x="0" y="0" width="10" height="10" fill="red"></rect>
            </g>
        </svg>
        """
        theme = ThemeFactory.create()

        with self.subTest(part="admin config"):
            url = reverse("admin:config_theme_change", args=(theme.pk,))

            change_page = self.app.get(url)

            upload = Upload(
                "bad_svg.svg", bad_svg_content.encode("utf-8"), "image/svg+xml"
            )

            form = change_page.forms["theme_form"]
            form["logo"] = upload
            response = form.submit()

            self.assertEqual(response.status_code, 302)
            theme.refresh_from_db()
            self.assertEqual(theme.logo, "logo/bad_svg.svg")

        with self.subTest(part="assert logo sanitized"):
            with theme.logo.file.open("r") as logo_file:
                # Assert that the logo is completely sanitized
                decoded_logo = logo_file.read().decode("utf-8")
                self.assertHTMLEqual(decoded_logo, sanitized_svg_content)

    def test_upload_png(self):
        logo = Path(settings.DJANGO_PROJECT_DIR) / "static" / "img" / "digid.png"
        theme = ThemeFactory.create()
        url = reverse("admin:config_theme_change", args=(theme.pk,))

        change_page = self.app.get(url)

        with open(logo, "rb") as infile:
            upload = Upload("digid.png", infile.read(), "image/png")

        form = change_page.forms["theme_form"]
        form["logo"] = upload
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        theme.refresh_from_db()
        self.assertEqual(theme.logo, "logo/digid.png")

    def test_upload_blank(self):
        # fixes #581
        theme = ThemeFactory.create()
        url = reverse("admin:config_theme_change", args=(theme.pk,))
        change_page = self.app.get(url)

        form = change_page.forms["theme_form"]
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        theme.refresh_from_db()
        self.assertEqual(theme.logo, "")

    def test_can_upload_stylesheet(self):
        theme = ThemeFactory.create()
        url = reverse("admin:config_theme_change", args=(theme.pk,))
        upload = Upload("my-theme.css", b".foo { display: block }", "text/css")

        change_page = self.app.get(url)

        form = change_page.forms["theme_form"]
        form["stylesheet_file"] = upload
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        theme.refresh_from_db()
        self.assertEqual(theme.stylesheet_file, "config/themes/my-theme.css")
