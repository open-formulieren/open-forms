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


class FormDesignerComponentTranslationTests(SeleniumTestCase):
    @classmethod
    def getWebdriverOptions(cls):
        options = super().getWebdriverOptions()
        options.add_argument("--lang=en-US")
        return options

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

    @override_settings(LANGUAGE_CODE="en")
    def test_editing_translatable_properties(self):
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
                        "key": "field1",
                        "label": "Field 1",
                        "description": "Description 1",
                    },
                    {
                        "type": "select",
                        "key": "field2",
                        "label": "Field 2",
                        "description": "Description 2",
                        "data": {
                            "values": [
                                {"value": "option1", "label": "Option 1"},
                                {"value": "option2", "label": "Option 2"},
                            ]
                        },
                    },
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
            component = self.selenium.find_element(
                By.CSS_SELECTOR,
                '[ref="component"].formio-component.formio-component-textfield',
            )
            scroll_into_view = (
                ActionChains(self.selenium)
                .scroll_to_element(component)
                .scroll_by_amount(
                    0, 80
                )  # handle the submit bar with position:sticky blocking the viewport
            )
            scroll_into_view.perform()
            # Formio? needs some time before the hover event can fire and be properly detected
            time.sleep(0.1)
            hover = ActionChains(self.selenium).move_to_element(component)
            hover.perform()
            # find the edit button and click it
            editButton = self.selenium.find_element(
                By.CSS_SELECTOR, '[ref="editComponent"]'
            )
            editButton.click()

            # ok, check that the modal is open
            try:
                self.selenium.find_element(By.CSS_SELECTOR, ".formio-dialog-content")
            except NoSuchElementException:
                self.fail("Modal was not opened")

        with phase("inspect textfield component translations"):
            # check the translations tab
            modal_tabs = self.selenium.find_elements(
                By.CSS_SELECTOR, ".formio-dialog-content .nav-link"
            )
            translations_tab = next(
                tab for tab in modal_tabs if tab.text == "Vertalingen"
            )
            translations_tab.click()
            time.sleep(0.1)  # some time for the translations to update

            # check the NL translations
            literal1 = self.selenium.find_element(
                By.NAME, "data[openForms.translations.nl][0]"
            )
            self.assertEqual(literal1.get_attribute("value"), "Field 1")
            translation1 = self.selenium.find_element(
                By.NAME, "data[openForms.translations.nl][0][translation]"
            )
            self.assertEqual(translation1.get_attribute("value"), "")

            literal2 = self.selenium.find_element(
                By.NAME, "data[openForms.translations.nl][1]"
            )
            self.assertEqual(literal2.get_attribute("value"), "Description 1")
            translation2 = self.selenium.find_element(
                By.NAME, "data[openForms.translations.nl][1][translation]"
            )
            self.assertEqual(translation2.get_attribute("value"), "")

        with phase("edit textfield label literal"):
            # edit a literal
            modal_tabs[0].click()
            label_input = self.selenium.find_element(By.NAME, "data[label]")
            label_input.clear()
            label_input.send_keys("Field label")

        with phase("inspect and update textfield component translations"):
            # back to the translations tab
            translations_tab.click()
            WebDriverWait(self.selenium, 1).until(
                EC.text_to_be_present_in_element_value(
                    (By.NAME, "data[openForms.translations.nl][0]"),
                    "Description 1",
                )
            )
            translation2 = self.selenium.find_element(
                By.NAME, "data[openForms.translations.nl][1][translation]"
            )
            translation2.clear()
            translation2.send_keys("Veldlabel")

        with phase("save textfield component changes"):
            modal_save_button = self.selenium.find_element(
                By.CSS_SELECTOR, '.formio-dialog-content [ref="saveButton"]'
            )
            modal_save_button.click()
            # allow sufficient time for the state/reducer to update everything & the modal to close
            WebDriverWait(self.selenium, 1).until_not(
                EC.visibility_of_any_elements_located(
                    (By.CSS_SELECTOR, ".formio-dialog-content")
                )
            )

        with phase("inspect select component translations"):
            select_selector = '[ref="dragComponent"]:nth-child(2)'
            component = self.selenium.find_element(By.CSS_SELECTOR, select_selector)
            scroll_into_view = (
                ActionChains(self.selenium)
                .scroll_to_element(component)
                .scroll_by_amount(
                    0, 80
                )  # handle the submit bar with position:sticky blocking the viewport
            )
            scroll_into_view.perform()
            # Formio? needs some time before the hover event can fire and be properly detected
            time.sleep(0.2)
            hover = ActionChains(self.selenium).move_to_element(component)
            hover.perform()
            # find the edit button and click it
            editButton = self.selenium.find_element(
                By.CSS_SELECTOR, f'{select_selector} [ref="editComponent"]'
            )
            editButton.click()

            modal_tabs = self.selenium.find_elements(
                By.CSS_SELECTOR, ".formio-dialog-content .nav-link"
            )
            translations_tab = next(
                tab for tab in modal_tabs if tab.text == "Vertalingen"
            )
            translations_tab.click()

            expected_literals = ["Field 2", "Description 2", "Option 1", "Option 2"]
            for index, literal in enumerate(expected_literals):
                with self.subTest(literal=literal, index=index):
                    WebDriverWait(self.selenium, 1).until(
                        EC.text_to_be_present_in_element_value(
                            (By.NAME, f"data[openForms.translations.nl][{index}]"),
                            literal,
                        )
                    )

            modal_cancel_button = self.selenium.find_element(
                By.CSS_SELECTOR, '.formio-dialog-content [ref="cancelButton"]'
            )
            modal_cancel_button.click()
            # allow sufficient time for the state/reducer to update everything & the modal to close
            WebDriverWait(self.selenium, 1).until_not(
                EC.visibility_of_any_elements_located(
                    (By.CSS_SELECTOR, ".formio-dialog-content")
                )
            )

        with phase("save form changes to backend"):
            save_button = self.selenium.find_element(By.NAME, "_save")
            save_button.click()
            # provide sufficient time for all the save actions to complete
            changelist_url = str(
                furl(self.live_server_url) / reverse("admin:forms_form_changelist")
            )
            WebDriverWait(self.selenium, 5).until(EC.url_to_be(changelist_url))

        with phase("check saved data in database"):
            # check the translations have been persisted
            translations = (
                form.formstep_set.get().form_definition.component_translations
            )
            self.assertEqual(
                translations,
                {
                    "nl": {"Field label": "Veldlabel"},
                    "en": {},
                },
            )
