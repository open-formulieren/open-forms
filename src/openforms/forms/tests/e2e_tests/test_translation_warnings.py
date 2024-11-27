from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser

from ..factories import FormFactory


class TranslationWarningTests(E2ETestCase):
    async def test_no_warning_for_components_with_missing_translations(self):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test nl",
                name_en="Playwright test en",
                explanation_template_nl="playwright test nl",
                explanation_template_en="playwright test en",
                begin_text_nl="playwright test nl",
                begin_text_en="playwright test en",
                previous_text_nl="playwright test nl",
                previous_text_en="playwright test en",
                change_text_nl="playwright test nl",
                change_text_en="playwright test en",
                confirm_text_nl="playwright test nl",
                confirm_text_en="playwright test en",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test nl",
                formstep__form_definition__name_en="Playwright test en",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "someField",
                            "label": "Some Field",
                            "openForms": {
                                "translations": {
                                    "en": {"label": ""},
                                    "nl": {"label": ""},
                                }
                            },
                        }
                    ],
                },
                translation_enabled=True,
            )
            ConfirmationEmailTemplateFactory.create(
                form=form,
                content_nl="Playwright test nl",
                content_en="Playwright test en",
                subject_nl="Playwright test nl",
                subject_en="Playwright test en",
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

            warning_list = page.locator("css=.messagelist")

            await expect(warning_list).not_to_be_visible()

    async def test_warning_with_empty_translations(self):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                name="Playwright test",
                name_nl="",
                name_en="",
                explanation_template_nl="",
                explanation_template_en="",
                begin_text_nl="",
                begin_text_en="",
                previous_text_nl="",
                previous_text_en="",
                change_text_nl="",
                change_text_en="",
                confirm_text_nl="",
                confirm_text_en="",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="",
                formstep__form_definition__name_en="",
                translation_enabled=True,
            )
            ConfirmationEmailTemplateFactory.create(
                form=form,
                content_nl="",
                content_en="",
                subject_nl="",
                subject_en="",
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

            warning_list = page.locator("css=.messagelist")
            await warning_list.get_by_role("link", name="8 translations").click()

            modal = page.locator("css=.react-modal__content")

            await expect(
                modal.get_by_role("row", name="Form Dutch name")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Form English name")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Steps and fields Dutch name")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Steps and fields English name")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Confirmation Dutch cosign subject")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Confirmation English cosign content")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Confirmation Dutch cosign subject")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Confirmation English cosign content")
            ).to_be_visible()

    async def test_warning_with_mixed_explanation_translations(self):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test nl",
                name_en="Playwright test en",
                explanation_template_nl="",
                explanation_template_en="playwright test en",
                begin_text_nl="playwright test nl",
                begin_text_en="playwright test en",
                previous_text_nl="playwright test nl",
                previous_text_en="playwright test en",
                change_text_nl="playwright test nl",
                change_text_en="playwright test en",
                confirm_text_nl="playwright test nl",
                confirm_text_en="playwright test en",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test nl",
                formstep__form_definition__name_en="Playwright test en",
                translation_enabled=True,
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
            warning_list = page.locator("css=.messagelist")
            await warning_list.get_by_role("link", name="1 translation").click()

            modal = page.locator("css=.react-modal__content")

            await expect(
                modal.get_by_role("row", name="Form Dutch explanation template")
            ).to_be_visible()

    async def test_warning_with_fall_backfields_and_only_default_language_translations(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test nl",
                name_en="Playwright test en",
                explanation_template_nl="playwright test nl",
                explanation_template_en="playwright test en",
                begin_text_nl="playwright test nl",
                begin_text_en="",
                previous_text_nl="playwright test nl",
                previous_text_en="",
                change_text_nl="playwright test nl",
                change_text_en="",
                confirm_text_nl="playwright test nl",
                confirm_text_en="",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test nl",
                formstep__form_definition__name_en="Playwright test en",
                translation_enabled=True,
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

            warning_list = page.locator("css=.messagelist")
            await warning_list.get_by_role("link", name="4 translation").click()

            modal = page.locator("css=.react-modal__content")

            await expect(
                modal.get_by_role("row", name="Literals English begin text")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Literals English step previous text")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Literals English change text")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Literals English confirm text")
            ).to_be_visible()

    async def test_no_warning_with_fall_backfields_and_only_none_default_language_translations(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test nl",
                name_en="Playwright test en",
                explanation_template_nl="playwright test nl",
                explanation_template_en="playwright test en",
                begin_text_nl="",
                begin_text_en="playwright test en",
                previous_text_nl="",
                previous_text_en="playwright test en",
                change_text_nl="",
                change_text_en="playwright test en",
                confirm_text_nl="",
                confirm_text_en="playwright test en",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test nl",
                formstep__form_definition__name_en="Playwright test en",
                translation_enabled=True,
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

            warning_list = page.locator("css=.messagelist")

            # expect nl fields to be taken from global config
            await expect(warning_list).not_to_be_visible()

    async def test_no_warning_for_confirmation_email_field_with_none_default_translations(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test nl",
                name_en="Playwright test en",
                explanation_template_nl="playwright test nl",
                explanation_template_en="playwright test en",
                begin_text_nl="playwright test nl",
                begin_text_en="playwright test en",
                previous_text_nl="playwright test nl",
                previous_text_en="playwright test en",
                change_text_nl="playwright test nl",
                change_text_en="playwright test en",
                confirm_text_nl="playwright test nl",
                confirm_text_en="playwright test en",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test nl",
                formstep__form_definition__name_en="Playwright test en",
                translation_enabled=True,
            )
            ConfirmationEmailTemplateFactory.create(
                form=form,
                content_nl="",
                content_en="Playwright test en",
                subject_nl="",
                subject_en="Playwright test en",
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

            warning_list = page.locator("css=.messagelist")

            # expect nl fields to be taken from global config
            await expect(warning_list).not_to_be_visible()

    async def test_warning_for_confirmation_email_field_with_only_dutch_translations(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test nl",
                name_en="Playwright test en",
                explanation_template_nl="playwright test nl",
                explanation_template_en="playwright test en",
                begin_text_nl="playwright test nl",
                begin_text_en="playwright test en",
                previous_text_nl="playwright test nl",
                previous_text_en="playwright test en",
                change_text_nl="playwright test nl",
                change_text_en="playwright test en",
                confirm_text_nl="playwright test nl",
                confirm_text_en="playwright test en",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test nl",
                formstep__form_definition__name_en="Playwright test en",
                translation_enabled=True,
            )
            ConfirmationEmailTemplateFactory.create(
                form=form,
                content_nl="Playwright test nl",
                content_en="",
                subject_nl="Playwright test nl",
                subject_en="",
                cosign_content_nl="Playwright test nl",
                cosign_content_en="",
                cosign_subject_nl="Playwright test nl",
                cosign_subject_en="",
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

            warning_list = page.locator("css=.messagelist")
            await warning_list.get_by_role("link", name="4 translation").click()

            modal = page.locator("css=.react-modal__content")

            await expect(
                modal.get_by_role("row", name="Confirmation English content")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Confirmation English Subject")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Confirmation English cosign content")
            ).to_be_visible()
            await expect(
                modal.get_by_role("row", name="Confirmation English cosign subject")
            ).to_be_visible()
