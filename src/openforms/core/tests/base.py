from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TEST_FORM_DEFINITION_CONFIG = {
    "components": [
        {
            "label": "Fieldy Field",
            "key": "fieldyField",
            "description": "",
            "conditional": {
                "show": None,
                "when": None,
                "eq": ""
            },
            "input": True,
            "placeholder": "",
            "prefix": "",
            "customClass": "",
            "suffix": "",
            "multiple": False,
            "defaultValue": None,
            "protected": False,
            "unique": False,
            "persistent": True,
            "hidden": False,
            "clearOnHide": True,
            "refreshOn": "",
            "redrawOn": "",
            "tableView": True,
            "modalEdit": False,
            "labelPosition": "top",
            "errorLabel": "",
            "tooltip": "",
            "hideLabel": False,
            "tabindex": "",
            "disabled": False,
            "autofocus": False,
            "dbIndex": False,
            "customDefaultValue": "",
            "calculateValue": "",
            "calculateServer": False,
            "widget": {
                "type": "input"
            },
            "attributes": {},
            "validateOn": "change",
            "validate": {
                "required": False,
                "custom": "",
                "customPrivate": False,
                "strictDateValidation": False,
                "multiple": False,
                "unique": False,
                "minLength": "",
                "maxLength": "",
                "pattern": ""
            },
            "overlay": {
                "style": "",
                "left": "",
                "top": "",
                "width": "",
                "height": ""
            },
            "allowCalculateOverride": False,
            "encrypted": False,
            "showCharCount": False,
            "showWordCount": False,
            "properties": {},
            "allowMultipleMasks": False,
            "type": "textfield",
            "mask": False,
            "inputType": "text",
            "inputFormat": "plain",
            "inputMask": "",
            "spellcheck": True,
            "id": "e0evwd"
        },
        {
            "label": "Checky",
            "key": "checky",
            "description": "",
            "input": True,
            "placeholder": "",
            "prefix": "",
            "customClass": "",
            "suffix": "",
            "multiple": False,
            "protected": False,
            "unique": False,
            "persistent": True,
            "hidden": False,
            "clearOnHide": True,
            "refreshOn": "",
            "redrawOn": "",
            "tableView": False,
            "modalEdit": False,
            "labelPosition": "right",
            "errorLabel": "",
            "tooltip": "",
            "hideLabel": False,
            "tabindex": "",
            "disabled": False,
            "autofocus": False,
            "dbIndex": False,
            "customDefaultValue": "",
            "calculateValue": "",
            "calculateServer": False,
            "widget": None,
            "attributes": {},
            "validateOn": "change",
            "validate": {
                "required": False,
                "custom": "",
                "customPrivate": False,
                "strictDateValidation": False,
                "multiple": False,
                "unique": False
            },
            "conditional": {
                "show": None,
                "when": None,
                "eq": ""
            },
            "overlay": {
                "style": "",
                "left": "",
                "top": "",
                "width": "",
                "height": ""
            },
            "allowCalculateOverride": False,
            "encrypted": False,
            "showCharCount": False,
            "showWordCount": False,
            "properties": {},
            "allowMultipleMasks": False,
            "type": "checkbox",
            "inputType": "checkbox",
            "dataGridLabel": True,
            "value": "",
            "name": "",
            "id": "ekyj0j",
            "defaultValue": False
        }
    ]
}


class SeleniumStepTestBase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        cls.selenium = webdriver.Chrome(chrome_options=chrome_options)
        cls.selenium.implicitly_wait(20)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="john",
            password="secret",
            email="john@example.com"
        )
        self.selenium.get('{}/admin/'.format(self.live_server_url))
        username = self.selenium.find_element_by_id('id_username')
        password = self.selenium.find_element_by_id('id_password')

        username.send_keys(self.user.username)
        password.send_keys('secret')

        submit = self.selenium.find_element_by_xpath('//input[@type="submit"]')
        submit.click()

    def tearDown(self) -> None:
        super().tearDown()
        WebDriverWait(self.selenium, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'html'))
        )
