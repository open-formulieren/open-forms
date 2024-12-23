from pathlib import Path
from unittest.mock import patch

from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect
from rest_framework.test import APIRequestFactory

from openforms.forms.tests.factories import FormFactory
from openforms.tests.e2e.base import E2ETestCase, browser_page

factory = APIRequestFactory()

TEST_FILES = Path(__file__).parent / "data"


class FillInFormTests(E2ETestCase):
    async def test_form_with_file_upload(self):
        # If using the ci.py settings locally, the SDK_RELEASE  variable should be set to 'latest', otherwise the
        # JS/CSS for the SDK will not be found (since they will be expected to be in the folder
        # openforms/static/sdk/<SDK version tag> instead of openforms/static/sdk
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Form with file upload",
                slug="form-with-file-upload",
                generate_minimal_setup=True,
                formstep__form_definition__name="First step",
                formstep__form_definition__slug="first-step",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "file",
                            "key": "fileUpload",
                            "label": "File Upload",
                            "storage": "url",
                            "validate": {
                                "required": True,
                            },
                        }
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

                async with page.expect_file_chooser() as fc_info:
                    await page.get_by_text("blader").click()

                file_chooser = await fc_info.value
                await file_chooser.set_files(TEST_FILES / "test.txt")

                await page.wait_for_load_state("networkidle")

                uploaded_file = page.get_by_role("link", name="test.txt")
                await expect(uploaded_file).to_be_visible()

                await page.get_by_role("button", name="Volgende").click()
                await page.get_by_role("button", name="Verzenden").click()
                await expect(
                    page.get_by_text("Een moment geduld", exact=False)
                ).to_be_visible()

    async def test_form_with_msg_file_upload(self):
        # If using the ci.py settings locally, the SDK_RELEASE  variable should be set to 'latest', otherwise the
        # JS/CSS for the SDK will not be found (since they will be expected to be in the folder
        # openforms/static/sdk/<SDK version tag> instead of openforms/static/sdk
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Form with file upload",
                slug="form-with-file-upload",
                generate_minimal_setup=True,
                formstep__form_definition__name="First step",
                formstep__form_definition__slug="first-step",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "file",
                            "key": "fileUpload",
                            "label": "File Upload",
                            "storage": "url",
                            "validate": {
                                "required": True,
                            },
                        }
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

                async with page.expect_file_chooser() as fc_info:
                    await page.get_by_text("blader").click()

                file_chooser = await fc_info.value
                await file_chooser.set_files(TEST_FILES / "test.msg")

                await page.wait_for_load_state("networkidle")

                uploaded_file = page.get_by_role("link", name="test.msg")
                await expect(uploaded_file).to_be_visible()

                await page.get_by_role("button", name="Volgende").click()
                await page.get_by_role("button", name="Verzenden").click()
                await expect(
                    page.get_by_text("Een moment geduld", exact=False)
                ).to_be_visible()
