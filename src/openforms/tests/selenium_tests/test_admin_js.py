"""
Tests for Javascript bundle running in the admin context.
"""
from django.urls import reverse

from furl import furl
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from openforms.accounts.tests.factories import SuperUserFactory

from .base import SeleniumTestCase


class GeneralAdminJSTests(SeleniumTestCase):
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
