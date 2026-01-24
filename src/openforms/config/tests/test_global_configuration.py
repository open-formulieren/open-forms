import json
import shutil
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import clamd
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from webtest import Form as WebTestForm, Upload

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.tests.utils import NOOP_CACHES

from ..models import GlobalConfiguration


def _ensure_arrayfields(form: WebTestForm, config: GlobalConfiguration | None = None):
    if config is None:
        config = GlobalConfiguration.get_solo()  # type: ignore
    # set the values manually, normally this is done through JS (django-jsonform takes
    # care of it)
    form["email_template_netloc_allowlist"] = json.dumps(
        config.email_template_netloc_allowlist
    )
    form["recipients_email_digest"] = json.dumps(config.recipients_email_digest)


@disable_admin_mfa()
@override_settings(
    CACHES=NOOP_CACHES,
    MEDIA_ROOT=tempfile.mkdtemp(),
    SESSION_ENGINE="django.contrib.sessions.backends.db",
)
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

    def test_plugin_configuration(self):
        # mocking the admin/solo machinery is not straightforward here...
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {
            "authentication": {
                "digid": {
                    "enabled": False,
                }
            }
        }
        config.save()
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        custom_widget = change_page.pyquery(".plugin-config-react")
        self.assertEqual(len(custom_widget), 1)
        self.assertEqual(custom_widget.attr("data-name"), "plugin_configuration")
        self.assertEqual(
            custom_widget.attr("data-value"),
            '{"authentication": {"digid": {"enabled": false}}}',
        )

        # introspect registry
        json_script = custom_widget.find("#plugin_configuration-modules-and-plugins")
        modules_and_plugins = json.loads(json_script.text())
        self.assertIn("authentication", modules_and_plugins)
        self.assertIn(
            {"identifier": "digid", "label": _("DigiD")},
            modules_and_plugins["authentication"],
        )

    def test_configuration_save_form_email_can_be_added(self):
        config = GlobalConfiguration.get_solo()
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        form = change_page.forms["globalconfiguration_form"]
        form["save_form_email_subject_nl"] = "Subject {{form_name}}"
        form["save_form_email_content_nl"] = "Content {{form_name}}"
        _ensure_arrayfields(form, config=config)
        form.submit()

        config.refresh_from_db()
        self.assertEqual(config.save_form_email_subject, "Subject {{form_name}}")
        self.assertEqual(config.save_form_email_content, "Content {{form_name}}")

    @override_settings(LANGUAGE_CODE="en")
    def test_virus_scan_enabled_not_configured(self):
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        form = change_page.forms["globalconfiguration_form"]
        form["enable_virus_scan"] = True
        _ensure_arrayfields(form)
        response = form.submit()

        self.assertEqual(200, response.status_code)

        html_soup = response.html

        error_node = html_soup.find("p", attrs={"class": "errornote"})

        self.assertIn("Please correct the error below", error_node.text)

        list_errors = html_soup.find("ul", attrs={"class": "errorlist"})

        self.assertEqual(
            list(list_errors.children)[0].text,
            "ClamAV host and port need to be configured if virus scan is enabled.",
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_virus_scan_enabled_cant_connect(self):
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        form = change_page.forms["globalconfiguration_form"]
        form["enable_virus_scan"] = True
        form["clamav_host"] = "clamav.bla"
        form["clamav_port"] = 3310

        with patch.object(
            clamd.ClamdNetworkSocket,
            "ping",
            side_effect=clamd.ConnectionError("Cannot connect!"),
        ):
            _ensure_arrayfields(form)
            response = form.submit()

        self.assertEqual(200, response.status_code)

        html_soup = response.html

        error_node = html_soup.find("p", attrs={"class": "errornote"})

        self.assertIn("Please correct the error below", error_node.text)

        list_errors = html_soup.find("ul", attrs={"class": "errorlist"})

        self.assertEqual(
            list(list_errors.children)[0].text,
            "Cannot connect to ClamAV: Cannot connect!",
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_svg_sanitation_favicon(self):
        bad_svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="25" fill="green" onclick="alert(\'forget about me?\')" />
            <script>//<![CDATA[
                alert("I am malicious >:)")
            //]]></script>
            <g>
                <rect class="btn" x="0" y="0" width="10" height="10" fill="red" onload="alert(\'click!\')" />
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

        config = GlobalConfiguration.get_solo()

        with self.subTest(part="admin config"):
            url = reverse("admin:config_globalconfiguration_change", args=(1,))
            change_page = self.app.get(url)

            upload = Upload(
                "bad_svg.svg", bad_svg_content.encode("utf-8"), "image/svg+xml"
            )

            form = change_page.forms["globalconfiguration_form"]
            form["favicon"] = upload
            _ensure_arrayfields(form, config=config)
            response = form.submit()

            self.assertEqual(response.status_code, 302)
            config.refresh_from_db()
            self.assertEqual(config.favicon, "logo/bad_svg.svg")

        with self.subTest(part="assert favicon sanitized"):
            with config.favicon.file.open("r") as favicon_file:
                # Assert that the logo is completely sanitized
                decoded_logo = favicon_file.read().decode("utf-8")
                self.assertHTMLEqual(decoded_logo, sanitized_svg_content)


class GlobalConfirmationEmailTests(TestCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(GlobalConfiguration.clear_cache)

        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["good.net"]
        config.save()

    def test_validate_content_syntax(self):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_content = "{{{}}}"

        with self.assertRaisesRegex(ValidationError, "Could not parse the remainder:"):
            config.full_clean()

    def test_validate_content_required_tags(self):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_content = "no tags here"
        with self.assertRaisesRegex(
            ValidationError,
            _("Missing required template-tag {tag}").format(
                tag="{% appointment_information %}"
            ),
        ):
            config.full_clean()

    def test_validate_content_netloc_sanitation_validation(self):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_content = "no tags here"

        with self.subTest("valid"):
            config.confirmation_email_content = "bla bla http://good.net/bla?x=1 {% appointment_information %} {% payment_information %}"

            config.full_clean()

        with self.subTest("invalid"):
            config.confirmation_email_content = "bla bla http://bad.net/bla?x=1 {% appointment_information %} {% payment_information %}"
            with self.assertRaisesMessage(
                ValidationError,
                _("This domain is not in the global netloc allowlist: {netloc}").format(
                    netloc="bad.net"
                ),
            ):
                config.full_clean()


class GlobalSaveFormEmailTests(TestCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(GlobalConfiguration.clear_cache)

        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["good.net"]
        config.save()

    def test_validate_content_syntax(self):
        config = GlobalConfiguration.get_solo()
        config.save_form_email_content = "{{{}}}"

        with self.assertRaisesRegex(ValidationError, "Could not parse the remainder:"):
            config.full_clean()

    def test_validate_content_netloc_sanitation_validation(self):
        config = GlobalConfiguration.get_solo()
        config.save_form_email_content = "no tags here"

        with self.subTest("valid"):
            config.save_form_email_content = "bla bla http://good.net/bla?x=1 {% appointment_information %} {% payment_information %} {% cosign_information %}"

            config.full_clean()

        with self.subTest("invalid"):
            config.save_form_email_content = "bla bla http://bad.net/bla?x=1 {% appointment_information %} {% payment_information %} {% cosign_information %}"
            with self.assertRaisesMessage(
                ValidationError,
                _("This domain is not in the global netloc allowlist: {netloc}").format(
                    netloc="bad.net"
                ),
            ):
                config.full_clean()
