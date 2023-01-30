import os
from unittest import skipIf

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings, tag
from django.utils.module_loading import import_string

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


@tag("selenium")
@skipIf(not WebDriver, "No Selenium webdriver configured")
@disable_2fa
@override_settings(ALLOWED_HOSTS=["*"])
class SeleniumTestCase(StaticLiveServerTestCase):
    @classmethod
    def getWebdriverOptions(cls):
        options = Options()  # type: ignore
        if SELENIUM_HEADLESS:
            options.headless = True
        return options

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        options = cls.getWebdriverOptions()
        cls.selenium = WebDriver(options=options)  # type: ignore
        cls.selenium.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()
