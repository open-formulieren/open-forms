from unittest.mock import patch

from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect
from rest_framework.test import APIRequestFactory

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.api.serializers import SubmissionSuspensionSerializer
from openforms.submissions.models import Submission
from openforms.tests.e2e.base import E2ETestCase, browser_page

factory = APIRequestFactory()


class ResumeFormTests(E2ETestCase):
    async def test_pause_and_resume_form(self):
        # If using the ci.py settings locally, the SDK_RELEASE  variable should be set to 'latest', otherwise the
        # JS/CSS for the SDK will not be found (since they will be expected to be in the folder
        # openforms/static/sdk/<SDK version tag> instead of openforms/static/sdk
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Form to save and resume",
                slug="form-to-pause-and-resume",
                generate_minimal_setup=True,
                formstep__form_definition__name="First step",
                formstep__form_definition__slug="first-step",
            )
            return form

        @sync_to_async
        def get_submission_uuid_and_resume_url(form, request, live_server):
            submission = Submission.objects.get(form=form)

            serializer = SubmissionSuspensionSerializer(context={"request": request})
            continue_url = furl(serializer.get_continue_url(submission))
            continue_url.origin = live_server
            return {"uuid": submission.uuid, "resume_url": continue_url.url}

        form = await setUpTestData()
        form_url = str(
            furl(self.live_server_url)
            / reverse("forms:form-detail", kwargs={"slug": form.slug})
        )

        request = factory.get("/foo")

        with patch("openforms.utils.validators.allow_redirect_url", return_value=True):
            async with browser_page() as page:
                await page.goto(form_url)

                await page.get_by_role("button", name="Formulier starten").click()

                await page.get_by_role("button", name="Tussentijds opslaan").click()

                await page.get_by_label("Je e-mailadres").fill("test@test.nl")

                await page.get_by_role("button", name="Later verdergaan").click()

                await page.wait_for_url(f"{form_url}startpagina")

                submission_info = await get_submission_uuid_and_resume_url(
                    form, request, self.live_server_url
                )

                await page.goto(submission_info["resume_url"])
                await page.wait_for_url(
                    f"{form_url}stap/first-step?submission_uuid={submission_info['uuid']}"
                )

                header = page.get_by_role("heading", name="First step")

                await expect(header).to_be_visible()
