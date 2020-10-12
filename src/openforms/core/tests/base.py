import mock

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumDisclosureStepTestBase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        cls.selenium = webdriver.Chrome(chrome_options=chrome_options)
        cls.selenium.implicitly_wait(20)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    @mock.patch('vips.accounts.gateways.gateway.send')
    def setUp(self, mocked_gateway) -> None:
        super().setUp()
        self.selenium.get('{}'.format(self.live_server_url))
        username = self.selenium.find_element_by_id('id_username')
        password = self.selenium.find_element_by_id('id_password')

        username.send_keys(self.user.username)
        password.send_keys('secret')

        submit = self.selenium.find_element_by_name('submit')
        submit.click()

        sent_token = mocked_gateway.call_args[1]['token']

        token = self.selenium.find_element_by_id('id_token')
        token.send_keys(sent_token)
        submit = self.selenium.find_element_by_name('submit')
        submit.click()

    def tearDown(self) -> None:
        super().tearDown()
        WebDriverWait(self.selenium, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'html'))
        )
