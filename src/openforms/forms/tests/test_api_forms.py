from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, tag
from django.urls import reverse
from django.utils import translation

from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from csp_post_processor.constants import NONCE_HTTP_HEADER
from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.config.models import GlobalConfiguration
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory

from ..api.serializers import FormSerializer
from ..constants import StatementCheckboxChoices
from ..models import Form
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory

PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
    b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
    b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FormSerializerTests(APITestCase):
    def test_public_fields_meta_exist_in_fields_meta(self):
        # catch changes
        for field in FormSerializer.Meta.public_fields:
            with self.subTest(field=field):
                self.assertIn(field, FormSerializer.Meta.fields)

    def test_get_fields_is_filtered_for_non_staff(self):
        request = APIRequestFactory().get("/")
        request.user = UserFactory()

        serializer = FormSerializer(context={"request": request})
        fields = serializer.get_fields()

        # everything returned by get_fields() should exist in Meta.public_fields
        for field in fields.keys():
            with self.subTest(field=field):
                self.assertIn(field, FormSerializer.Meta.public_fields)

    def test_get_fields_is_not_filtered_for_staff(self):
        request = APIRequestFactory().get("/")
        request.user = StaffUserFactory()

        serializer = FormSerializer(context={"request": request})
        fields = serializer.get_fields()

        # everything returned by get_fields() should exist in Meta.fields
        for field in fields.keys():
            with self.subTest(field=field):
                self.assertIn(field, FormSerializer.Meta.fields)

    def test_get_resume_link_lifetime(self):
        form1 = FormFactory.create(
            incomplete_submissions_removal_limit=7, all_submissions_removal_limit=10
        )
        form2 = FormFactory.create(
            incomplete_submissions_removal_limit=7, all_submissions_removal_limit=5
        )

        url1 = reverse("api:form-detail", kwargs={"uuid_or_slug": form1.slug})
        url2 = reverse("api:form-detail", kwargs={"uuid_or_slug": form2.slug})

        response_data1 = self.client.get(url1).json()
        response_data2 = self.client.get(url2).json()

        with self.subTest("All submissions > incomplete submission"):
            self.assertEqual(response_data1["resumeLinkLifetime"], 7)

        with self.subTest("All submissions < incomplete submission"):
            self.assertEqual(response_data2["resumeLinkLifetime"], 5)

        form3 = FormFactory.create(incomplete_submissions_removal_limit=7)
        url3 = reverse("api:form-detail", kwargs={"uuid_or_slug": form3.slug})

        with patch(
            "openforms.forms.api.serializers.form.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(all_submissions_removal_limit=10),
        ):
            response_data3 = self.client.get(url3).json()

        with self.subTest("Global > form specific"):
            self.assertEqual(response_data3["resumeLinkLifetime"], 7)

        with patch(
            "openforms.forms.api.serializers.form.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(all_submissions_removal_limit=5),
        ):
            response_data4 = self.client.get(url3).json()

        with self.subTest("Global < form specific"):
            self.assertEqual(response_data4["resumeLinkLifetime"], 5)

        form4 = FormFactory.create()
        url4 = reverse("api:form-detail", kwargs={"uuid_or_slug": form4.slug})

        with patch(
            "openforms.forms.api.serializers.form.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(incomplete_submissions_removal_limit=7),
        ):
            response_data5 = self.client.get(url4).json()

        with self.subTest("No form specific setting"):
            self.assertEqual(response_data5["resumeLinkLifetime"], 7)

    @override_settings(LANGUAGE_CODE="en")
    def test_statement_checkboxes_configuration_defaults(self):
        request = APIRequestFactory().get("/")
        request.user = AnonymousUser()
        config = GlobalConfiguration(
            ask_privacy_consent=True,
            privacy_policy_url="http://example-privacy.com",
            privacy_policy_label="I read the {% privacy_policy %}",
            ask_statement_of_truth=True,
            statement_of_truth_label="I am honest",
        )
        form = FormFactory.create()
        with patch(
            "openforms.forms.api.serializers.form.GlobalConfiguration.get_solo",
            return_value=config,
        ):
            serializer = FormSerializer(instance=form, context={"request": request})
            configuration = serializer.data["submission_statements_configuration"]

        self.assertEqual(len(configuration), 2)
        privacy_checkbox, truth_checkbox = configuration

        with self.subTest("privacy_checkbox"):
            self.assertTrue(privacy_checkbox["validate"]["required"])
            self.assertHTMLEqual(
                'I read the <a href="http://example-privacy.com" target="_blank" '
                'rel="noreferrer noopener">privacy policy</a>',
                privacy_checkbox["label"],
            )
            self.assertEqual(privacy_checkbox["key"], "privacyPolicyAccepted")

        with self.subTest("truth_checkbox"):
            self.assertTrue(truth_checkbox["validate"]["required"])
            self.assertHTMLEqual(
                "I am honest",
                truth_checkbox["label"],
            )
            self.assertEqual(truth_checkbox["key"], "statementOfTruthAccepted")

    @override_settings(LANGUAGE_CODE="en")
    def test_statement_checkboxes_configuration_not_required_with_overrides(self):
        request = APIRequestFactory().get("/")
        request.user = AnonymousUser()
        config = GlobalConfiguration(
            ask_privacy_consent=False, ask_statement_of_truth=False
        )
        form = FormFactory.create(
            ask_privacy_consent=StatementCheckboxChoices.required,
            ask_statement_of_truth=StatementCheckboxChoices.required,
        )
        with patch(
            "openforms.forms.api.serializers.form.GlobalConfiguration.get_solo",
            return_value=config,
        ):
            serializer = FormSerializer(instance=form, context={"request": request})
            configuration = serializer.data["submission_statements_configuration"]

        self.assertEqual(len(configuration), 2)
        privacy_checkbox, truth_checkbox = configuration

        with self.subTest("privacy_checkbox"):
            self.assertTrue(privacy_checkbox["validate"]["required"])
            self.assertEqual(privacy_checkbox["key"], "privacyPolicyAccepted")

        with self.subTest("truth_checkbox"):
            self.assertTrue(truth_checkbox["validate"]["required"])
            self.assertEqual(truth_checkbox["key"], "statementOfTruthAccepted")

    @override_settings(LANGUAGE_CODE="en")
    def test_statement_checkboxes_configuration_required_with_overrides(self):
        request = APIRequestFactory().get("/")
        request.user = AnonymousUser()
        config = GlobalConfiguration(
            ask_privacy_consent=True, ask_statement_of_truth=True
        )
        form = FormFactory.create(
            ask_privacy_consent=StatementCheckboxChoices.disabled,
            ask_statement_of_truth=StatementCheckboxChoices.disabled,
        )
        with patch(
            "openforms.forms.api.serializers.form.GlobalConfiguration.get_solo",
            return_value=config,
        ):
            serializer = FormSerializer(instance=form, context={"request": request})
            configuration = serializer.data["submission_statements_configuration"]

        self.assertEqual(len(configuration), 2)
        privacy_checkbox, truth_checkbox = configuration

        with self.subTest("privacy_checkbox"):
            self.assertFalse(privacy_checkbox["validate"]["required"])
            self.assertEqual(privacy_checkbox["key"], "privacyPolicyAccepted")

        with self.subTest("truth_checkbox"):
            self.assertFalse(truth_checkbox["validate"]["required"])
            self.assertEqual(truth_checkbox["key"], "statementOfTruthAccepted")


class FormsAPITests(APITestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory.create()
        self.client.force_authenticate(user=self.user)
        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_logo_details(self):
        form = FormFactory.create(authentication_backend="digid")
        form_definition = FormDefinitionFactory.create()
        FormStepFactory.create(form=form, form_definition=form_definition)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        logo = response.data["login_options"][0]["logo"]
        self.assertEqual(logo["title"], "DigiD")
        self.assertEqual(
            logo["image_src"], "http://testserver/static/img/digid-46x46.png"
        )
        self.assertEqual(logo["href"], "https://www.digid.nl/")
        self.assertEqual(logo["appearance"], "dark")

    def test_include_confirmation_page_content_in_pdf_exposed(self):
        """Assert that the option to include the confirmation page content in the
        submission PDF is exposed via the API if and only if the client is staff"""
        form = FormFactory.create(
            include_confirmation_page_content_in_pdf=False,
        )
        form_definition = FormDefinitionFactory.create()
        FormStepFactory.create(form=form, form_definition=form_definition)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        # non-staff users don't have access to the relevant info
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotIn("includeConfirmationPageContentInPdf", response.json())

        # staff users have access to the relevant info
        self.user.is_staff = True
        self.user.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("includeConfirmationPageContentInPdf", response.json())

    def test_non_staff_cant_access_deleted_form(self):
        form = FormFactory.create(deleted_=True)

        response = self.client.get(
            reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_cant_access_deleted_form(self):
        form = FormFactory.create(deleted_=True)

        response = self.client.get(
            reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_form_by_uuid(self):
        form = FormFactory.create()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["uuid"], str(form.uuid))

    def test_retrieve_form_by_slug(self):
        form = FormFactory.create()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.slug})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["slug"], form.slug)

    def test_not_retrieve_inactive_anon(self):
        self.client.logout()
        form = FormFactory.create(active=False)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_inactive_staff(self):
        form = FormFactory.create(active=False)

        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_retrieve_deleted_anon(self):
        self.client.logout()
        form = FormFactory.create(deleted_=True)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_not_retrieve_deleted(self):
        form = FormFactory.create(deleted_=True)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_deleted_staff(self):
        form = FormFactory.create(deleted_=True)
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_maintenance_mode_value_returned_through_api(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["maintenanceMode"], False)

    def test_global_config_text_field_values_returned_through_api(self):
        # set the defaults to compare
        config = GlobalConfiguration.get_solo()
        config.form_begin_text = "Begin form"
        config.form_previous_text = "Previous page"
        config.form_change_text = "Change"
        config.form_confirm_text = "Confirm"
        config.save()

        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        literals_data = response.json()["literals"]
        self.assertEqual(literals_data["beginText"]["resolved"], "Begin form")
        self.assertEqual(literals_data["beginText"]["value"], "")
        self.assertEqual(literals_data["previousText"]["resolved"], "Previous page")
        self.assertEqual(literals_data["previousText"]["value"], "")
        self.assertEqual(literals_data["changeText"]["resolved"], "Change")
        self.assertEqual(literals_data["changeText"]["value"], "")
        self.assertEqual(literals_data["confirmText"]["resolved"], "Confirm")
        self.assertEqual(literals_data["confirmText"]["value"], "")

    def test_global_config_steps_text_field_values_returned_through_api(self):
        # set the defaults to compare
        config = GlobalConfiguration.get_solo()
        config.form_step_previous_text = "Previous page"
        config.form_step_save_text = "Save current information"
        config.form_step_next_text = "Next"
        config.save()

        form = FormFactory.create()
        FormStepFactory.create(form=form)
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        step_literals_data = response.json()["steps"][0]["literals"]
        self.assertEqual(
            step_literals_data["previousText"]["resolved"], "Previous page"
        )
        self.assertEqual(step_literals_data["previousText"]["value"], "")
        self.assertEqual(
            step_literals_data["saveText"]["resolved"], "Save current information"
        )
        self.assertEqual(step_literals_data["saveText"]["value"], "")
        self.assertEqual(step_literals_data["nextText"]["resolved"], "Next")
        self.assertEqual(step_literals_data["nextText"]["value"], "")

    def test_global_config_communication_preferences_portal_url_value_returned_through_api(
        self,
    ):
        config = GlobalConfiguration.get_solo()
        config.communication_preferences_portal_url = "https://example-portal-url.com"
        config.save()

        form = FormFactory.create()
        FormStepFactory.create(form=form)
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["communicationPreferencesPortalUrl"],
            "https://example-portal-url.com",
        )

    def test_overridden_text_field_values_returned_through_api(self):
        form = FormFactory.create(
            begin_text="Overridden Begin Text",
            previous_text="Overridden Previous Text",
            change_text="Overridden Change Text",
            confirm_text="Overridden Confirm Text",
        )
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        literals_data = response.json()["literals"]
        self.assertEqual(
            literals_data["beginText"]["resolved"], "Overridden Begin Text"
        )
        self.assertEqual(literals_data["beginText"]["value"], "Overridden Begin Text")
        self.assertEqual(
            literals_data["previousText"]["resolved"], "Overridden Previous Text"
        )
        self.assertEqual(
            literals_data["previousText"]["value"], "Overridden Previous Text"
        )
        self.assertEqual(
            literals_data["changeText"]["resolved"], "Overridden Change Text"
        )
        self.assertEqual(literals_data["changeText"]["value"], "Overridden Change Text")
        self.assertEqual(
            literals_data["confirmText"]["resolved"], "Overridden Confirm Text"
        )
        self.assertEqual(
            literals_data["confirmText"]["value"], "Overridden Confirm Text"
        )

    def test_overridden_steps_text_field_values_returned_through_api(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            previous_text="Overridden Previous Text",
            save_text="Overridden Save Text",
            next_text="Overridden Next Text",
        )
        # self.client.logout()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        step_literals_data = response.json()["steps"][0]["literals"]
        self.assertEqual(
            step_literals_data["previousText"]["resolved"],
            "Overridden Previous Text",
        )
        self.assertEqual(
            step_literals_data["previousText"]["value"], "Overridden Previous Text"
        )
        self.assertEqual(
            step_literals_data["saveText"]["resolved"], "Overridden Save Text"
        )
        self.assertEqual(
            step_literals_data["saveText"]["value"], "Overridden Save Text"
        )
        self.assertEqual(
            step_literals_data["nextText"]["resolved"], "Overridden Next Text"
        )
        self.assertEqual(
            step_literals_data["nextText"]["value"], "Overridden Next Text"
        )

    def test_getting_a_form_with_a_confirmation_email_template(self):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Initial subject",
            content="Initial content",
        )
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["confirmationEmailTemplate"],
            {
                "subject": "Initial subject",
                "content": "Initial content",
                "cosignContent": "",
                "cosignSubject": "",
                "translations": {
                    "en": {
                        "content": "",
                        "subject": "",
                        "cosignContent": "",
                        "cosignSubject": "",
                    },
                    "nl": {
                        "content": "Initial content",
                        "subject": "Initial subject",
                        "cosignContent": "",
                        "cosignSubject": "",
                    },
                },
            },
        )

    @patch("csp_post_processor.processor.get_html_id")
    @tag("gh-5730", "gh-6113")
    def test_table_markup_in_explanation_template_not_mangled(self, mock_get_html_id):
        self.maxDiff = None
        mock_get_html_id.side_effect = ("1", "2", "3", "4")
        form = FormFactory.create(
            # HTML input taken from database after adding a table with TinyMCE
            explanation_template="""
                <table style="border-collapse: collapse; width: 100%;" border="1">
                    <colgroup>
                        <col style="width: 25%;">
                        <col style="width: 75%;">
                    </colgroup>
                    <tbody>
                        <tr>
                            <td>Tab</td>
                            <td style="border-style: none;">El</td>
                        </tr>
                    </tbody>
                </table>
            """,
            generate_minimal_setup=True,
        )
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url, headers={"X-CSP-Nonce": "dGVzdA=="})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertHTMLEqual(
            response.json()["explanationTemplate"],
            """
            <style nonce="dGVzdA==">
                #nonce-5fa62ae6176f3746142503a6ebe96cb3-1 { border-collapse: collapse;width: 100%; }
                #nonce-5fa62ae6176f3746142503a6ebe96cb3-2 { width: 25%; }
                #nonce-5fa62ae6176f3746142503a6ebe96cb3-3 { width: 75%; }
                #nonce-5fa62ae6176f3746142503a6ebe96cb3-4 { border-style: none; }
            </style>
            <table id="nonce-5fa62ae6176f3746142503a6ebe96cb3-1">
                <colgroup>
                    <col id="nonce-5fa62ae6176f3746142503a6ebe96cb3-2">
                    <col id="nonce-5fa62ae6176f3746142503a6ebe96cb3-3">
                </colgroup>
                <tbody>
                    <tr>
                        <td>Tab</td>
                        <td id="nonce-5fa62ae6176f3746142503a6ebe96cb3-4">El</td>
                    </tr>
                </tbody>
            </table>
            """,
        )

    def test_get_help_callout_page(self):
        form = FormFactory.create(help_callout_page_display="before_start_page")

        config = GlobalConfiguration.get_solo()
        config.help_callout_page_content = """
            <p>Some content</p>
            <a onclick="evil();">text</a>
        """
        config.help_callout_page_image = SimpleUploadedFile(
            "some_image.png", b"Some bytes", content_type="image/png"
        )
        config.save()

        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response_data = self.client.get(
            url, headers={NONCE_HTTP_HEADER: "some nonce"}
        ).json()

        expected_content = """
        <p>Some content</p>
        <a>text</a>
        """

        self.assertEqual(
            "before_start_page", response_data["helpCalloutPage"]["display"]
        )
        self.assertHTMLEqual(
            expected_content, response_data["helpCalloutPage"]["content"]
        )
        self.assertTrue(
            response_data["helpCalloutPage"]["image"].startswith(
                "http://testserver/media/help-callout-page/some_image",
            )
        )


class HelpDialogFormsAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create(is_staff=True, is_superuser=True)

    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.user)

    def _schedule_cleanup(self, form: Form):
        if not form.help_dialog_image.name:
            return

        self.addCleanup(
            lambda: form.help_dialog_image.storage.delete(form.help_dialog_image.name)
        )

    def test_retrieve_form_with_help_dialog_configured(self):
        form = FormFactory.create(
            help_dialog_content="Content with <strong>minimal</strong> tags.",
            help_dialog_image=ContentFile(content=PIXEL_PNG, name="pixel.png"),
        )
        self._schedule_cleanup(form)
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        help_dialog = response.json()["helpDialog"]
        self.assertIsInstance(help_dialog, dict)
        self.assertEqual(
            help_dialog["content"], "Content with <strong>minimal</strong> tags."
        )
        self.assertEqual(
            help_dialog["image"],
            f"http://testserver{form.help_dialog_image.url}",
        )


class FormsAPITranslationTests(APITestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        with translation.override("en"):
            cls.en_form = FormFactory.create(
                name="Form 1",
                begin_text="start",
                previous_text="prev",
                change_text="change",
                confirm_text="confirm",
            )
            ConfirmationEmailTemplateFactory.create(
                form=cls.en_form,
                subject="Initial subject",
                content="Initial content",
            )
            FormStepFactory.create(
                form=cls.en_form,
                next_text="Next",
                previous_text="Previous",
                save_text="Save",
            )

        cls.user = StaffUserFactory.create(user_permissions=["change_form"])

    def setUp(self):
        super().setUp()

        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_detail_shows_translated_values_based_on_request_header(self):
        with translation.override("en"):
            form = FormFactory.create(
                translation_enabled=True,
                begin_text="start",
                previous_text="prev",
                change_text="change",
                confirm_text="confirm",
                help_dialog_content="help dialog",
            )

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers["Content-Language"], "en")
        data = response.json()

        self.assertTrue(data["name"])  # it has a name from the factory

        def literal_value(field):
            return data["literals"][field]["value"]

        self.assertEqual(literal_value("beginText"), "start")
        self.assertEqual(literal_value("previousText"), "prev")
        self.assertEqual(literal_value("changeText"), "change")
        self.assertEqual(literal_value("confirmText"), "confirm")

        self.assertEqual(data["helpDialog"]["content"], "help dialog")

    @patch(
        "openforms.forms.models.utils.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            form_begin_text_en="Begin form",
            form_begin_text_nl="Dutch",
            form_previous_text_en="English",
            form_previous_text_nl="Dutch",
        ),
    )
    def test_detail_shows_translated_literals_use_global_defaults(self, *m):
        en_nl_combos = (
            ("", "Start formulier"),
            ("", ""),
            ("", None),
            (None, ""),
            (None, "Start formulier"),
        )

        for en, nl in en_nl_combos:
            with self.subTest(begin_text_en=en, begin_text_nl=nl):
                form = FormFactory.create(
                    translation_enabled=True,
                    begin_text_en=en,
                    begin_text_nl=nl,  # should always be ignored
                    previous_text_en="",
                    previous_text_nl="",
                    change_text="",
                    confirm_text="",
                )

                url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

                response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.headers["Content-Language"], "en")
                data = response.json()

                self.assertTrue(data["name"])  # it has a name from the factory

                self.assertEqual(
                    data["literals"]["beginText"]["resolved"], "Begin form"
                )
                self.assertEqual(
                    data["literals"]["previousText"]["resolved"], "English"
                )

    def test_detail_shows_translated_values_based_on_cookie(self):
        # request the api for Dutch, with a browser that negotiates English
        lang_url = reverse("api:i18n:language")
        response = self.client.put(
            lang_url, data={"code": "nl"}, HTTP_ACCEPT_LANGUAGE="en"
        )

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": self.en_form.uuid})
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers["Content-Language"], "nl")
        form = response.json()

        # The form is only translated into English
        # assert all values of this Dutch one are empty
        self.assertTrue(
            all(literal["value"] == "" for literal in form["literals"].values())
        )

    def test_activate_default_language_translation_enabled_false(self):
        """
        Default language should be set, because translation is disabled (ignoring any language headers)
        """
        form = FormFactory.create(translation_enabled=False)
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Language"], "nl")
        self.assertIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)

        language_cookie = response.cookies[settings.LANGUAGE_COOKIE_NAME]

        self.assertEqual(language_cookie.key, settings.LANGUAGE_COOKIE_NAME)
        self.assertEqual(language_cookie.value, "nl")
        self.assertEqual(language_cookie["expires"], "")
        self.assertEqual(language_cookie["path"], "/")
        self.assertEqual(language_cookie["comment"], "")
        self.assertEqual(language_cookie["domain"], "")
        self.assertEqual(language_cookie["max-age"], "")
        self.assertEqual(language_cookie["httponly"], True)
        self.assertEqual(language_cookie["version"], "")
        self.assertEqual(language_cookie["samesite"], settings.LANGUAGE_COOKIE_SAMESITE)
        self.assertEqual(translation.get_language(), settings.LANGUAGE_CODE)

    def test_activate_default_language_translation_enabled_true(self):
        """
        Endpoint should do nothing in this case, because translation is enabled
        """
        form = FormFactory.create(translation_enabled=True)
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Language"], "en")
        self.assertNotIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)
        self.assertEqual(translation.get_language(), "en")

    def test_detail_staff_show_translations(self):
        """
        Translations for all available languages should be returned for staff users, because they are relevant for the form design UI
        """
        self.user = UserFactory.create(is_staff=True)
        self.client.force_authenticate(user=self.user)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": self.en_form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["translations"],
            {
                "en": {
                    "begin_text": "start",
                    "change_text": "change",
                    "confirm_text": "confirm",
                    "introduction_page_content": "",
                    "explanation_template": "",
                    "name": "Form 1",
                    "previous_text": "prev",
                    "submission_confirmation_template": "",
                    "help_dialog_content": "",
                },
                "nl": {
                    "begin_text": "",
                    "change_text": "",
                    "confirm_text": "",
                    "introduction_page_content": "",
                    "explanation_template": "",
                    "name": "",
                    "previous_text": "",
                    "submission_confirmation_template": "",
                    "help_dialog_content": "",
                },
            },
        )
        self.assertEqual(
            response.data["confirmation_email_template"]["translations"],
            {
                "en": {
                    "subject": "Initial subject",
                    "content": "Initial content",
                    "cosign_content": "",
                    "cosign_subject": "",
                },
                "nl": {
                    "subject": "",
                    "content": "",
                    "cosign_content": "",
                    "cosign_subject": "",
                },
            },
        )

    def test_detail_non_staff_no_translations(self):
        """
        Translations for different languages than the active language should not be returned for non-staff users
        """
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": self.en_form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("translations", response.data)
        self.assertNotIn("translations", response.data["steps"][0]["literals"])

    def test_help_callout_page_content(self):
        form = FormFactory.create(translation_enabled=True)

        config = GlobalConfiguration.get_solo()
        config.help_callout_page_content_nl = "Nederlands"
        config.help_callout_page_content_en = "English"
        config.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        for language, expected in (("nl", "Nederlands"), ("en", "English")):
            with self.subTest(language=language):
                response = self.client.get(url, headers={"Accept-Language": language})

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.headers["Content-Language"], language)
                data = response.json()
                self.assertEqual(expected, data["helpCalloutPage"]["content"])
