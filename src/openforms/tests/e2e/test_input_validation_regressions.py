from django.test import override_settings, tag
from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.forms.tests.factories import FormFactory

from .base import E2ETestCase, browser_page


# allow all origins, since we don't know exactly the generated live server port number
@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
class InputValidationRegressionTests(E2ETestCase):

    @tag("gh-4065")
    async def test_hidden_components_validation(self):

        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                slug="validation",
                generate_minimal_setup=True,
                registration_backend=None,
                translation_enabled=False,  # force Dutch
                ask_privacy_consent=False,
                ask_statement_of_truth=False,
                formstep__next_text="Volgende",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "textfield",
                            "label": "Visible text field",
                            "validate": {"required": True},
                        },
                        {
                            "type": "number",
                            "key": "number",
                            "label": "Hidden number, clearOnHide",
                            "validate": {"required": True},
                            "hidden": True,
                            "clearOnHide": True,
                        },
                        {
                            "type": "date",
                            "key": "date",
                            "label": "Hidden number, no clearOnHide",
                            "validate": {"required": True},
                            "hidden": True,
                            "clearOnHide": False,
                            "defaultValue": "2024-03-27",
                        },
                        {
                            "type": "bsn",
                            "key": "bsn",
                            "label": "Conditionally hidden",
                            "validate": {"required": True},
                            "conditional": {
                                "show": True,
                                "when": "textfield",
                                "eq": "show me the bsn",
                            },
                            "clearOnHide": False,
                            "defaultValue": "123456781",  # invalid
                        },
                    ]
                },
            )
            return form

        form = await setUpTestData()
        form_url = str(
            furl(self.live_server_url)
            / reverse("forms:form-detail", kwargs={"slug": form.slug})
        )

        async with browser_page() as page:
            await page.goto(form_url)
            # Start the form
            await page.get_by_role("button", name="Formulier starten").click()

            # Fill out the visible field
            await page.get_by_label("Visible text field").fill("testing")
            await page.get_by_role("button", name="Volgende").click()

            # Confirm and finish the form
            await page.get_by_role("button", name="Verzenden").click()
            await expect(
                page.get_by_text("Een moment geduld", exact=False)
            ).to_be_visible()

    @tag("gh-4068")
    async def test_optional_fields(self):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                slug="validation",
                generate_minimal_setup=True,
                registration_backend=None,
                translation_enabled=False,  # force Dutch
                ask_privacy_consent=False,
                ask_statement_of_truth=False,
                formstep__next_text="Volgende",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "date",
                            "key": "date",
                            "label": "Optional date",
                            "validate": {"required": False},
                        },
                        {
                            "type": "textfield",
                            "key": "manyTextfield",
                            "label": "Optional Text fields",
                            "validate": {"required": False},
                            "multiple": True,
                            "defaultValue": [
                                None
                            ],  # The default value of multiple text fields
                        },
                        {
                            "type": "editgrid",
                            "key": "optionalRepeatingGroup",
                            "label": "Optional repeating group",
                            "validate": {"required": False},
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "optionalTextfield",
                                    "label": "Optional Text field",
                                    "validate": {"required": False},
                                }
                            ],
                        },
                    ]
                },
            )
            return form

        form = await setUpTestData()
        form_url = str(
            furl(self.live_server_url)
            / reverse("forms:form-detail", kwargs={"slug": form.slug})
        )

        async with browser_page() as page:
            await page.goto(form_url)
            # Start the form
            await page.get_by_role("button", name="Formulier starten").click()

            # Everything is optional, don't fill anything out
            await page.get_by_role("button", name="Volgende").click()

            # Confirm and finish the form
            await page.get_by_role("button", name="Verzenden").click()
            await expect(
                page.get_by_text("Een moment geduld", exact=False)
            ).to_be_visible()

    @tag("gh-4068")
    async def test_repeating_group(self):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                slug="validation",
                generate_minimal_setup=True,
                registration_backend=None,
                translation_enabled=False,  # force Dutch
                ask_privacy_consent=False,
                ask_statement_of_truth=False,
                formstep__next_text="Volgende",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "editgrid",
                            "key": "Optional repeating group",
                            "validate": {"required": False},
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "optionalTextfield",
                                    "label": "Optional Text field",
                                    "validate": {"required": False},
                                }
                            ],
                        }
                    ]
                },
            )
            return form

        form = await setUpTestData()
        form_url = str(
            furl(self.live_server_url)
            / reverse("forms:form-detail", kwargs={"slug": form.slug})
        )

        async with browser_page() as page:
            await page.goto(form_url)
            # Start the form
            await page.get_by_role("button", name="Formulier starten").click()

            # Fill in the repeating group
            await page.get_by_role("button", name="Nog één toevoegen").click()
            "Optional Text field"
            await page.get_by_label("Optional Text field").fill("testing")
            await page.get_by_role("button", name="Opslaan", exact=True).click()
            await page.get_by_role("button", name="Volgende").click()

            # Confirm and finish the form
            await page.get_by_role("button", name="Verzenden").click()
            await expect(
                page.get_by_text("Een moment geduld", exact=False)
            ).to_be_visible()
