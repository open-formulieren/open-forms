import re
from decimal import Decimal
from unittest.mock import patch

from django.urls import resolve, reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import Route, expect
from rest_framework.test import APIRequestFactory

from openforms.forms.constants import StatementCheckboxChoices
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.constants import ProcessingStatuses
from openforms.submissions.models import Submission
from openforms.tests.e2e.base import E2ETestCase, browser_page
from openforms.tests.e2e.database_sync_to_async import database_sync_to_async

factory = APIRequestFactory()


class PaymentFlowTests(E2ETestCase):
    @sync_to_async
    def get_form_url(self):
        # set up a form
        form = FormFactory.create(
            name="Form to pay",
            slug="form-to-pay",
            generate_minimal_setup=True,
            formstep__form_definition__name="First step",
            formstep__form_definition__slug="first-step",
            payment_backend="demo",
            product__price=Decimal("11.35"),
            ask_privacy_consent=StatementCheckboxChoices.disabled,
            ask_statement_of_truth=StatementCheckboxChoices.disabled,
        )

        return form

    @database_sync_to_async
    def set_submission_reference(self) -> None:
        # Required as payment will use the submission ref.
        submission = Submission.objects.last()
        submission.public_registration_reference = "OF-123456"
        submission.save()

    async def mock_status_url(self, route: Route):
        response = await route.fetch()
        json = await response.json()
        await self.set_submission_reference()

        json["status"] = ProcessingStatuses.done
        submission_uuid = resolve(furl(route.request.url).path).kwargs["uuid"]
        json["paymentUrl"] = str(
            furl(self.live_server_url)
            / reverse(
                "payments:start", kwargs={"uuid": submission_uuid, "plugin_id": "demo"}
            )
        )
        await route.fulfill(response=response, json=json)

    async def test_payment_flow(self):
        async with browser_page() as page:
            form = await self.get_form_url()
            form_url = str(
                furl(self.live_server_url)
                / reverse("forms:form-detail", kwargs={"slug": form.slug})
            )

            await page.route(
                re.compile(r"api/v2/submissions/.+?/status"), self.mock_status_url
            )
            await page.goto(form_url)

            with (
                patch(
                    "openforms.utils.validators.allow_redirect_url", return_value=True
                ),
                patch("openforms.payments.views.allow_redirect_url", return_value=True),
            ):
                await page.wait_for_url(f"{form_url}startpagina")

                payment_step = page.get_by_role("link", name="Betalen")

                await expect(payment_step).to_be_visible()

                await page.get_by_role("button", name="Formulier starten").click()
                await page.get_by_role("button", name="Volgende").click()
                await page.get_by_role("button", name="Verzenden").click()
                await page.get_by_role("button", name="Betalen").click()

                await page.wait_for_url(f"{form_url}bevestiging")

                # The reference won't be present because we are not running Celery
                await expect(page.get_by_role("heading")).to_contain_text(
                    "Bevestiging: "
                )

                payment_specific_text = page.get_by_text("De betaling is ontvangen.")

                await expect(payment_specific_text).to_be_visible()
