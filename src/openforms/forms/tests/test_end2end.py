import os
from importlib import import_module

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import RequestFactory
from django.urls import reverse

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from openforms.accounts.tests.factories import UserFactory

from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


class End2EndTestCase(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        webdriver = os.environ.get(
            "SELENIUM_DRIVER", "selenium.webdriver.chrome.webdriver"
        )
        webdriver_module = import_module(webdriver)
        options = webdriver_module.Options()
        options.headless = True

        cls.selenium = webdriver_module.WebDriver(options=options)
        cls.selenium.set_window_size(1920, 1080)
        cls.selenium.implicitly_wait(20)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.wait = WebDriverWait(self.selenium, 200)

        self.user = UserFactory.create(
            username="testuser", is_superuser=True, is_staff=True, password="secret"
        )

    def test_form_list_not_logged_in(self):
        FormFactory.create()

        self.selenium.get(
            "{}{}".format(self.live_server_url, reverse("forms:form-list"))
        )

        log_message = self.selenium.get_log("browser")[-1]["message"]
        self.assertTrue(log_message.endswith("403 (Forbidden)"))

    def test_form_list_logged_in(self):
        form = FormFactory.create()

        factory = RequestFactory()
        request = factory.get("/")
        self.client.login(
            username=self.user.username, password="secret", request=request
        )
        cookie = self.client.cookies[settings.SESSION_COOKIE_NAME]

        self.selenium.get("{}{}".format(self.live_server_url, reverse("admin:index")))
        self.selenium.add_cookie(
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": cookie.value,
                "secure": False,
                "path": "/",
            }
        )
        self.selenium.refresh()
        self.selenium.get("{}{}".format(self.live_server_url, reverse("admin:index")))

        self.selenium.get(
            "{}{}".format(self.live_server_url, reverse("forms:form-list"))
        )

        form_link = self.selenium.find_element_by_xpath("//main//ul//a")

        form_detail_path = reverse("forms:form-detail", kwargs={"slug": form.slug})
        self.assertEqual(
            form_link.get_attribute("href"), f"{self.live_server_url}{form_detail_path}"
        )

    # def test_submit_form(self):
    #     form = FormFactory.create()
    #     form_definition_1 = FormDefinitionFactory.create(
    #         configuration={
    #             "display": "form",
    #             "components": [
    #                 {
    #                     "id": "eqi2sq8",
    #                     "key": "textArea",
    #                     "mask": False,
    #                     "rows": 3,
    #                     "type": "textarea",
    #                     "input": True,
    #                     "label": "Text Area",
    #                     "editor": "",
    #                     "hidden": False,
    #                     "prefix": "",
    #                     "suffix": "",
    #                     "unique": False,
    #                     "widget": {"type": "input"},
    #                     "dbIndex": False,
    #                     "overlay": {
    #                         "top": "",
    #                         "left": "",
    #                         "style": "",
    #                         "width": "",
    #                         "height": "",
    #                     },
    #                     "tooltip": "",
    #                     "wysiwyg": False,
    #                     "disabled": False,
    #                     "multiple": False,
    #                     "redrawOn": "",
    #                     "tabindex": "",
    #                     "validate": {
    #                         "custom": "",
    #                         "unique": False,
    #                         "pattern": "",
    #                         "plugins": [],
    #                         "maxWords": "",
    #                         "minWords": "",
    #                         "multiple": False,
    #                         "required": False,
    #                         "maxLength": "",
    #                         "minLength": "",
    #                         "customPrivate": False,
    #                         "strictDateValidation": False,
    #                     },
    #                     "autofocus": False,
    #                     "encrypted": False,
    #                     "fixedSize": True,
    #                     "hideLabel": False,
    #                     "inputMask": "",
    #                     "inputType": "text",
    #                     "modalEdit": False,
    #                     "protected": False,
    #                     "refreshOn": "",
    #                     "tableView": True,
    #                     "attributes": {},
    #                     "errorLabel": "",
    #                     "persistent": True,
    #                     "properties": {},
    #                     "spellcheck": True,
    #                     "validateOn": "change",
    #                     "clearOnHide": True,
    #                     "conditional": {"eq": "", "show": None, "when": None},
    #                     "customClass": "",
    #                     "description": "",
    #                     "inputFormat": "html",
    #                     "placeholder": "",
    #                     "showInEmail": False,
    #                     "defaultValue": None,
    #                     "dataGridLabel": False,
    #                     "labelPosition": "top",
    #                     "showCharCount": False,
    #                     "showWordCount": False,
    #                     "calculateValue": "",
    #                     "calculateServer": False,
    #                     "isSensitiveData": False,
    #                     "allowMultipleMasks": False,
    #                     "customDefaultValue": "",
    #                     "allowCalculateOverride": False,
    #                 },
    #             ],
    #         }
    #     )
    #     FormStepFactory.create(form=form, form_definition=form_definition_1)

    #     self.selenium.get(
    #         "{}{}".format(
    #             self.live_server_url,
    #             reverse("forms:form-detail", kwargs={"slug": form.slug}),
    #         )
    #     )
    #     button = self.selenium.find_element_by_class_name("openforms-button")
    #     button.click()

    #     # Allow cookies
    #     # cookie_form = WebDriverWait(self.selenium, 40).until(
    #     #     EC.presence_of_element_located(
    #     #         (
    #     #             By.CLASS_NAME,
    #     #             'cookie-notice__form',
    #     #         )
    #     #     )
    #     # )
    #     # cookie_form.find_element_by_class_name("button").click()

    #     # textarea = WebDriverWait(self.selenium, 10).until(
    #     #     EC.presence_of_element_located(
    #     #         (
    #     #             By.XPATH,
    #     #             '//textarea',
    #     #         )
    #     #     )
    #     # )
    #     textarea = self.selenium.find_element_by_xpath('//textarea')
    #     textarea.send_keys("foo")

    #     # submit = WebDriverWait(self.selenium, 10).until(
    #     #     EC.presence_of_element_located(
    #     #         (
    #     #             By.XPATH,
    #     #             '//button[@type="submit" and @name="next" and not(@aria-disabled)]',
    #     #         )
    #     #     )
    #     # )
    #     submit = self.selenium.find_element_by_xpath('//button[@type="submit" and @name="next" and not(@aria-disabled)]')
    #     submit.click()

    #     summary_rows = self.selenium.find_elements_by_class_name(
    #         "openforms-summary-row"
    #     )

    #     self.assertEqual(len(summary_rows), 1)

    #     row = summary_rows[0]
    #     fieldname, value = row.find_elements_by_class_name("openforms-body")
    #     self.assertEqual(fieldname.text, "Text Area")
    #     self.assertEqual(value.text, "foo")

    #     privacy_checkbox = self.selenium.find_element_by_id("privacy")
    #     privacy_checkbox.click()

    #     confirm = self.selenium.find_element_by_xpath(
    #         '//button[@type="submit" and @name="confirm"]'
    #     )
    #     confirm.click()

    #     # download_icon = WebDriverWait(self.selenium, 40).until(
    #     #     EC.presence_of_element_located((By.CLASS_NAME, "fa-download"))
    #     # )
    #     download_icon = self.selenium.find_element_by_class_name('fa-download')

    #     self.assertIsNotNone(download_icon)

    def test_empty_filefield_confirmation_page(self):
        """
        Regression test for https://github.com/open-formulieren/open-forms/issues/1203
        """

        form = FormFactory.create()
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "id": "ekcq3op",
                        "key": "file",
                        "url": f"{self.live_server_url}/api/v1/submissions/files/upload",
                        "file": {"name": "", "type": []},
                        "type": "file",
                        "image": False,
                        "input": True,
                        "label": "File Upload",
                        "hidden": False,
                        "prefix": "",
                        "suffix": "",
                        "unique": False,
                        "webcam": False,
                        "widget": None,
                        "dbIndex": False,
                        "options": '{"withCredentials": True}',
                        "overlay": {
                            "top": "",
                            "left": "",
                            "style": "",
                            "width": "",
                            "height": "",
                        },
                        "storage": "url",
                        "tooltip": "",
                        "disabled": False,
                        "multiple": False,
                        "redrawOn": "",
                        "tabindex": "",
                        "validate": {
                            "custom": "",
                            "unique": False,
                            "multiple": False,
                            "required": False,
                            "customPrivate": False,
                            "strictDateValidation": False,
                        },
                        "autofocus": False,
                        "encrypted": False,
                        "hideLabel": False,
                        "imageSize": "200",
                        "modalEdit": False,
                        "protected": False,
                        "refreshOn": "",
                        "tableView": False,
                        "attributes": {},
                        "errorLabel": "",
                        "persistent": True,
                        "properties": {},
                        "uploadOnly": False,
                        "validateOn": "change",
                        "clearOnHide": True,
                        "conditional": {"eq": "", "show": None, "when": None},
                        "customClass": "",
                        "description": "",
                        "fileMaxSize": "1GB",
                        "fileMinSize": "0KB",
                        "filePattern": "",
                        "placeholder": "",
                        "showInEmail": False,
                        "defaultValue": [],
                        "dataGridLabel": False,
                        "labelPosition": "top",
                        "showCharCount": False,
                        "showWordCount": False,
                        "calculateValue": "",
                        "calculateServer": False,
                        "isSensitiveData": True,
                        "privateDownload": False,
                        "allowMultipleMasks": False,
                        "customDefaultValue": "",
                        "allowCalculateOverride": False,
                    }
                ],
            }
        )
        FormStepFactory.create(form=form, form_definition=form_definition_1)

        # Form start page
        self.selenium.get(
            "{}{}".format(
                self.live_server_url,
                reverse("forms:form-detail", kwargs={"slug": form.slug}),
            )
        )
        button = self.selenium.find_element_by_class_name("openforms-button")
        button.click()

        # Allow cookies
        # cookie_form = WebDriverWait(self.selenium, 10).until(
        #     EC.presence_of_element_located(
        #         (
        #             By.CLASS_NAME,
        #             'cookie-notice__form',
        #         )
        #     )
        # )
        cookie_form = self.selenium.find_element_by_class_name('cookie-notice__form')
        cookie_form.find_element_by_class_name("button").click()

        # First form step
        # submit = WebDriverWait(self.selenium, 10).until(
        #     EC.presence_of_element_located(
        #         (
        #             By.XPATH,
        #             '//button[@type="submit" and @name="next" and not(@aria-disabled)]',
        #         )
        #     )
        # )
        submit = self.selenium.find_element_by_xpath('//button[@type="submit" and @name="next" and not(@aria-disabled)]')
        submit.click()

        # Confirmation page
        summary_rows = self.selenium.find_elements_by_class_name(
            "openforms-summary-row"
        )

        # Filefield should appear in the summary
        self.assertEqual(len(summary_rows), 1)

        row = summary_rows[0]
        fieldname, value = row.find_elements_by_class_name("openforms-body")
        self.assertEqual(fieldname.text, "File Upload")
        self.assertEqual(value.text, "(leeg)")

        privacy_checkbox = self.selenium.find_element_by_id("privacy")
        self.assertIsNotNone(privacy_checkbox)

        confirm = self.selenium.find_element_by_xpath(
            '//button[@type="submit" and @name="confirm"]'
        )
        self.assertIsNotNone(confirm)
