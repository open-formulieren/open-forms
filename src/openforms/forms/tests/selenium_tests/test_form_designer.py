import time
from contextlib import contextmanager

from django.test import override_settings
from django.urls import reverse

from furl import furl
from selenium.common import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.tests.selenium_tests.base import SeleniumTestCase

from ..factories import FormFactory


@contextmanager
def phase(desc: str):
    yield


class FormDesignerKeyValidationTest(SeleniumTestCase):
    def setUp(self):
        super().setUp()

        SuperUserFactory.create(username="admin", password="selenium")

        # log the super user in to the admin
        login_url = furl(self.live_server_url) / reverse("admin:login")
        self.selenium.get(str(login_url))
        username_input = self.selenium.find_element(By.ID, "id_username")
        username_input.send_keys("admin")
        password_input = self.selenium.find_element(By.ID, "id_password")
        password_input.send_keys("selenium")
        self.selenium.find_element(
            By.XPATH, '//input[@type="submit"][not(@hidden)]'
        ).click()

    @override_settings(LANGUAGE_CODE="nl")
    def test_regex_validation_key(self):
        # set up a form
        form = FormFactory.create(
            name="Selenium test",
            name_nl="Selenium test",
            generate_minimal_setup=True,
            formstep__form_definition__name_nl="Selenium test",
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "someField",
                        "label": "Some Field",
                    }
                ],
            },
        )
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        # load the change page
        self.selenium.get(admin_url)

        with phase("Activate steps/fields tab"):
            # navigate to the "steps and fields" tab
            all_tabs = self.selenium.find_elements(By.CSS_SELECTOR, '[role="tab"]')
            steps_tab = next(tab for tab in all_tabs if tab.text == "Steps and fields")
            steps_tab.click()

        with phase("Open textfield component edit modal"):
            # find the formio component and hover over it to make the actions visible
            textfield_component = self.selenium.find_element(
                By.CSS_SELECTOR,
                ".builder-component",
            )
            scroll_into_view = (
                ActionChains(self.selenium)
                .scroll_to_element(textfield_component)
                .scroll_by_amount(
                    0, 80
                )  # handle the submit bar with position:sticky blocking the viewport
            )
            scroll_into_view.perform()
            # Formio? needs some time before the hover event can fire and be properly detected
            time.sleep(0.2)
            hover = ActionChains(self.selenium).move_to_element(textfield_component)
            hover.perform()
            # find the edit button and click it
            editButton = textfield_component.find_element(
                By.CSS_SELECTOR, '[ref="editComponent"]'
            )
            editButton.click()

            # ok, check that the modal is open
            try:
                self.selenium.find_element(By.CSS_SELECTOR, ".formio-dialog-content")
            except NoSuchElementException:
                self.fail("Modal was not opened")

        with phase("Update component key with invalid characters"):
            key_input_field = self.selenium.find_element(By.NAME, "data[key]")

            time.sleep(0.2)  # Field takes a while to be active
            fill_invalid_key = (
                ActionChains(self.selenium)
                .move_to_element(key_input_field)
                .click()
                .send_keys(" +?!")  # invalid characters
            )
            fill_invalid_key.perform()
            time.sleep(0.2)  # Validation seems to take a while

            parent = key_input_field.find_element(By.XPATH, "../..")
            parent_classes = parent.get_attribute("class").split(" ")

            self.assertIn("has-error", parent_classes)
            self.assertIn("has-message", parent_classes)

            error_field = parent.find_element(
                By.CSS_SELECTOR, "div.form-text:nth-child(1)"
            )

            self.assertEqual(
                "De eigenschapsnaam mag alleen alfanumerieke tekens, onderstrepingstekens, punten en streepjes "
                "bevatten en mag niet worden afgesloten met een streepje of punt.",
                error_field.text,
            )
