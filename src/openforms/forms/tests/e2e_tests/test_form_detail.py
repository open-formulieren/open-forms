from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser

from ..factories import FormFactory


class FormDesignerComponentTranslationTests(E2ETestCase):
    async def test_editing_translatable_properties(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Form with confirmation email",
                name_nl="Formulier met bevestigingsemail",
                generate_minimal_setup=True,
                send_confirmation_email=True,
            )
            ConfirmationEmailTemplateFactory.create(
                subject="Custom Subject",
                content="Custom content {% appointment_information %} {% payment_information %} {% cosign_information %}",
                form=form,
            )
            return form

        await create_superuser()
        form = await setUpTestData()
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await page.get_by_role("tab", name="Confirmation").click()

            confirmation_email_template_node = page.locator(
                "css=.confirmation-email-template"
            )

            await expect(confirmation_email_template_node).to_be_visible()

            # Uncheck the checkbox
            await page.get_by_label("Send confirmation email").click()

            await expect(confirmation_email_template_node).to_be_hidden()

            # Save the form
            await page.locator('[name="_save"]').click()

        @sync_to_async
        def get_refreshed_form_and_template(form):
            form.refresh_from_db()
            return form, form.confirmation_email_template

        form, email_template = await get_refreshed_form_and_template(form)

        self.assertFalse(form.send_confirmation_email)
        self.assertEqual(email_template.subject, "")
        self.assertEqual(email_template.content, "")
