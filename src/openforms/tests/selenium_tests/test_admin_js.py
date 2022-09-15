"""
Tests for Javascript bundle running in the admin context.
"""
import os
from unittest import skipIf

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.urls import reverse
from django.utils.module_loading import import_string

from furl import furl
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.tests.utils import disable_2fa

SELENIUM_WEBDRIVER = os.getenv("SELENIUM_WEBDRIVER", default="Chrome")
SELENIUM_HEADLESS = "NO_SELENIUM_HEADLESS" not in os.environ

if SELENIUM_WEBDRIVER:
    WebDriver = import_string(f"selenium.webdriver.{SELENIUM_WEBDRIVER}")
    Options = import_string(
        f"selenium.webdriver.{SELENIUM_WEBDRIVER.lower()}.options.Options"
    )
else:
    WebDriver, Options = None, None


@skipIf(not WebDriver, "No Selenium webdriver configured")
@disable_2fa
@override_settings(ALLOWED_HOSTS=["*"])
class GeneralAdminJSTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        options = Options()
        if SELENIUM_HEADLESS:
            options.headless = True

        cls.selenium = WebDriver(options=options)
        cls.selenium.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_admin_pages_with_js_bundle_dont_crash(self):
        SuperUserFactory.create(username="admin", password="selenium")

        # list of URLs that are known to include the Webpack admin JS bundle
        page_urls = (
            reverse("admin:forms_form_add"),
            reverse("admin:forms_formdefinition_add"),
            reverse("admin:config_globalconfiguration_change", args=(1,)),
        )

        # authenticate
        login_url = furl(self.live_server_url) / reverse("admin:login")
        self.selenium.get(str(login_url))
        username_input = self.selenium.find_element(By.ID, "id_username")
        username_input.send_keys("admin")
        password_input = self.selenium.find_element(By.ID, "id_password")
        password_input.send_keys("selenium")
        self.selenium.find_element(
            By.XPATH, '//input[@type="submit"][not(@hidden)]'
        ).click()

        for page_path in page_urls:
            with self.subTest(admin_url=page_path):
                full_url = furl(self.live_server_url) / page_path

                self.selenium.get(str(full_url))

                try:
                    self.selenium.find_element(By.ID, "selenium-test-id")
                except NoSuchElementException:
                    self.fail(
                        "The Javascript on the admin page didn't succeed in writing "
                        "the Selenium marker node, probably the JS is crashing on "
                        "that page."
                    )
