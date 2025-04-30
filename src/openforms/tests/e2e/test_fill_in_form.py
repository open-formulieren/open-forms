from unittest.mock import patch

from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.forms.tests.factories import FormFactory

from .base import E2ETestCase, browser_page


class FillInFormTests(E2ETestCase):
    async def test_normal_and_nested_data_text_fields(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Form nested data",
                slug="form-with-nested-data",
                generate_minimal_setup=True,
                formstep__form_definition__name="First step",
                formstep__form_definition__slug="first-step",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "text.field",
                            "label": "Text field nested",
                        },
                        {
                            "type": "textfield",
                            "key": "textfield",
                            "label": "Text field non-nested",
                        },
                    ]
                },
                translation_enabled=False,  # force Dutch
                ask_privacy_consent=False,
                ask_statement_of_truth=False,
            )
            return form

        form = await setUpTestData()
        form_url = str(
            furl(self.live_server_url)
            / reverse("forms:form-detail", kwargs={"slug": form.slug})
        )

        with patch("openforms.utils.validators.allow_redirect_url", return_value=True):
            async with browser_page() as page:
                await page.goto(form_url)

                await page.get_by_role("button", name="Formulier starten").click()

                await page.get_by_label("Text field nested").fill("This is nested data")
                await page.get_by_label("Text field non-nested").fill(
                    "This is non-nested data"
                )

                await page.get_by_role("button", name="Volgende").click()

                with self.subTest("Nested data"):
                    await expect(
                        page.get_by_text("This is nested data")
                    ).to_be_visible()

                with self.subTest("Non-nested data"):
                    await expect(
                        page.get_by_text("This is non-nested data")
                    ).to_be_visible()
