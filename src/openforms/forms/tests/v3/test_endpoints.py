from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.config.tests.factories import ThemeFactory
from openforms.data_removal.constants import RemovalMethods
from openforms.forms.constants import StatementCheckboxChoices, SubmissionAllowedChoices
from openforms.forms.models.form import Form
from openforms.forms.tests.factories import CategoryFactory, FormFactory
from openforms.products.tests.factories import ProductFactory


class FormEndpointTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = UserFactory.create(
            is_staff=True, user_permissions=("forms.change_form",)
        )

    def setUp(self) -> None:
        super().setUp()

        self.client.force_authenticate(user=self.admin_user)

    def test_create_minimal_form(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "maintenanceMode": True,
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.name, "Create form")
        self.assertEqual(form.slug, "create-form")
        self.assertEqual(form.maintenance_mode, True)

    def test_create_detailed_form(self):
        product = ProductFactory.create()
        category = CategoryFactory.create()
        theme = ThemeFactory.create()
        activate_on = timezone.now() + timedelta(days=1)
        deactivate_on = timezone.now() + timedelta(days=2)
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "internalName": "Create form internal",
            "internalRemarks": "This form is used for xyz",
            "translationEnabled": True,
            "appointmentOptions": {
                "isAppointment": True,
            },
            "literals": {
                "beginText": {"value": "Different Begin Text"},
                "previousText": {"value": "Different Previous Text"},
                "changeText": {"value": "Different Change Text"},
                "confirmText": {"value": "Different Confirm Text"},
            },
            "product": product.uuid,
            "slug": "create-form",
            "category": category.uuid,
            "theme": theme.uuid,
            "showProgressIndicator": True,
            "showSummaryProgress": True,
            "maintenanceMode": True,
            "active": True,
            "activateOn": activate_on.isoformat(),
            "deactivateOn": deactivate_on.isoformat(),
            "isDeleted": False,
            "submissionConfirmationTemplate": "Have a cookie",
            "introductionPageContent": "You can ask for cookies here",
            "explanationTemplate": "Get ready to ask for some cookies",
            "submissionAllowed": SubmissionAllowedChoices.yes,
            "submissionLimit": 10,
            "submissionCounter": 0,
            "suspensionAllowed": True,
            "askPrivacyConsent": StatementCheckboxChoices.required,
            "askStatementOfTruth": StatementCheckboxChoices.required,
            "submissionsRemovalOptions": {
                "successfulSubmissionsRemovalLimit": 10,
                "successfulSubmissionsRemovalMethod": RemovalMethods.delete_permanently,
                "incompleteSubmissionsRemovalLimit": 5,
                "incompleteSubmissionsRemovalMethod": RemovalMethods.delete_permanently,
                "erroredSubmissionsRemovalLimit": 20,
                "erroredSubmissionsRemovalMethod": RemovalMethods.delete_permanently,
                "allSubmissionsRemovalLimit": 30,
            },
            "confirmationEmailTemplate": {
                "translations": {
                    "en": {
                        "subject": "Submission received",
                        "content": "{% confirmation_summary %} {% appointment_information %} {% payment_information %}",
                        "cosign_subject": "Cosign submission received",
                        "cosign_content": "{% confirmation_summary %} {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                    "nl": {
                        "subject": "Inzending ontvangen",
                        "content": "{% confirmation_summary %} {% appointment_information %} {% payment_information %}",
                        "cosign_subject": "Cosign inzending ontvangen",
                        "cosign_content": "{% confirmation_summary %} {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                }
            },
            "sendConfirmationEmail": True,
            "displayMainWebsiteLink": True,
            "includeConfirmationPageContentInPdf": True,
            "translations": {
                "en": {
                    "name": "Create form",
                    "beginText": "start",
                    "previousText": "previous",
                    "changeText": "change",
                    "confirmText": "confirm",
                    "submissionConfirmationTemplate": "Have a cookie",
                    "introductionPageContent": "You can ask for cookies here",
                    "explanationTemplate": "Get ready to ask for some cookies",
                },
                "nl": {
                    "name": "Create formulier",
                    "beginText": "start",
                    "previousText": "vorige",
                    "changeText": "wijzigen",
                    "confirmText": "bevestigen",
                    "submissionConfirmationTemplate": "Neem een koekje",
                    "introductionPageContent": "Je kan hier voor koekjes vragen",
                    "explanationTemplate": "Wees klaar om voor koekjes te vragen",
                },
            },
            "newRendererEnabled": True,
            "newLogicEvaluationEnabled": True,
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.name_en, "Create form")
        self.assertEqual(form.name_nl, "Create formulier")
        self.assertEqual(form.internal_name, "Create form internal")
        self.assertEqual(form.internal_remarks, "This form is used for xyz")
        self.assertFalse(form.login_required)
        self.assertTrue(form.translation_enabled)

        self.assertTrue(form.is_appointment)
        self.assertEqual(form.slug, "create-form")

        # product
        self.assertEqual(form.product, product)

        # category
        category = form.category
        self.assertEqual(form.category, category)

        # theme
        theme = form.theme
        self.assertEqual(form.theme, theme)

        self.assertTrue(form.show_progress_indicator)
        self.assertTrue(form.show_summary_progress)
        self.assertTrue(form.maintenance_mode)
        self.assertTrue(form.active)
        self.assertEqual(form.activate_on, activate_on)
        self.assertEqual(form.deactivate_on, deactivate_on)
        self.assertFalse(form._is_deleted)
        self.assertEqual(form.submission_confirmation_template, "Neem een koekje")
        self.assertEqual(
            form.introduction_page_content, "Je kan hier voor koekjes vragen"
        )
        self.assertEqual(
            form.explanation_template, "Wees klaar om voor koekjes te vragen"
        )
        self.assertEqual(form.submission_allowed, SubmissionAllowedChoices.yes)
        self.assertEqual(form.submission_limit, 10)
        self.assertEqual(form.submission_counter, 0)
        self.assertTrue(form.suspension_allowed)
        self.assertEqual(form.ask_privacy_consent, StatementCheckboxChoices.required)
        self.assertEqual(form.ask_statement_of_truth, StatementCheckboxChoices.required)
        self.assertEqual(form.successful_submissions_removal_limit, 10)
        self.assertEqual(
            form.successful_submissions_removal_method,
            RemovalMethods.delete_permanently,
        )
        self.assertEqual(form.incomplete_submissions_removal_limit, 5)
        self.assertEqual(
            form.incomplete_submissions_removal_method,
            RemovalMethods.delete_permanently,
        )
        self.assertEqual(form.errored_submissions_removal_limit, 20)
        self.assertEqual(
            form.errored_submissions_removal_method, RemovalMethods.delete_permanently
        )
        self.assertEqual(form.all_submissions_removal_limit, 30)
        self.assertTrue(form.send_confirmation_email)
        self.assertTrue(form.display_main_website_link)
        self.assertTrue(form.include_confirmation_page_content_in_pdf)

        # confirmation email
        confirmation_email_template = form.confirmation_email_template
        assert confirmation_email_template, "No confirmation email coupled to form"
        self.assertEqual(confirmation_email_template.subject_en, "Submission received")
        self.assertEqual(
            confirmation_email_template.content_en,
            "{% confirmation_summary %} {% appointment_information %} {% payment_information %}",
        )
        self.assertEqual(
            confirmation_email_template.cosign_subject_en, "Cosign submission received"
        )
        self.assertEqual(
            confirmation_email_template.cosign_content_en,
            "{% confirmation_summary %} {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )
        self.assertEqual(confirmation_email_template.subject_nl, "Inzending ontvangen")
        self.assertEqual(
            confirmation_email_template.content_nl,
            "{% confirmation_summary %} {% appointment_information %} {% payment_information %}",
        )
        self.assertEqual(
            confirmation_email_template.cosign_subject_nl, "Cosign inzending ontvangen"
        )
        self.assertEqual(
            confirmation_email_template.cosign_content_nl,
            "{% confirmation_summary %} {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

        # translations
        self.assertEqual(form.begin_text_en, "start")
        self.assertEqual(form.previous_text_en, "previous")
        self.assertEqual(form.change_text_en, "change")
        self.assertEqual(form.confirm_text_en, "confirm")
        self.assertEqual(form.submission_confirmation_template_en, "Have a cookie")
        self.assertEqual(
            form.introduction_page_content_en, "You can ask for cookies here"
        )
        self.assertEqual(
            form.explanation_template_en, "Get ready to ask for some cookies"
        )
        self.assertEqual(form.begin_text_nl, "start")
        self.assertEqual(form.previous_text_nl, "vorige")
        self.assertEqual(form.change_text_nl, "wijzigen")
        self.assertEqual(form.confirm_text_nl, "bevestigen")
        self.assertEqual(form.submission_confirmation_template_nl, "Neem een koekje")
        self.assertEqual(
            form.introduction_page_content_nl, "Je kan hier voor koekjes vragen"
        )
        self.assertEqual(
            form.explanation_template_nl, "Wees klaar om voor koekjes te vragen"
        )

        self.assertTrue(form.new_renderer_enabled)

    def test_create_form_incorrect_request(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "Create-form",
            "literals": "foobar",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)
        response_data = response.json()
        assert "invalidParams" in response_data
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0]["name"], "literals.nonFieldErrors"
        )

    def test_update_existing_form(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        self.assertEqual(form.name, "Update form")
        self.assertEqual(form.slug, "update-form")

    def test_update_soft_deleted_form(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
            active=True,
            deleted_=True,
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        self.assertEqual(form.name, "Update form")
        self.assertEqual(form.slug, "update-form")
        self.assertTrue(form._is_deleted)

    def test_update_form_incorrect_request(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
            "literals": "foobar",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        assert "invalidParams" in response_data
        self.assertEqual(len(response_data["invalidParams"]), 1)
        self.assertEqual(response_data["invalidParams"][0]["code"], "invalid")
        self.assertEqual(
            response_data["invalidParams"][0]["name"], "literals.nonFieldErrors"
        )

        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()
        self.assertEqual(form.name, "Create form")
        self.assertIsNone(form.previous_text_nl)
        self.assertIsNone(form.previous_text_en)
        self.assertIsNone(form.begin_text_nl)
        self.assertIsNone(form.begin_text_en)
        self.assertIsNone(form.change_text_nl)
        self.assertIsNone(form.change_text_en)
        self.assertIsNone(form.confirm_text_nl)
        self.assertIsNone(form.confirm_text_en)

    def test_inactive_form(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
            active=False,
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form.refresh_from_db()

        self.assertEqual(form.name, "Update form")
        self.assertEqual(form.slug, "update-form")
        self.assertFalse(form.active)

    def test_unsupported_patch(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
        )

        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Form.objects.count(), 1)

    def test_unsupported_post(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "maintenanceMode": True,
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Form.objects.count(), 0)


class FormEndpointAccessTests(APITestCase):
    def test_non_staff_user(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "maintenanceMode": True,
        }

        non_staff_user = UserFactory.create(is_staff=False, user_permissions=tuple())
        self.client.force_login(non_staff_user)
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Form.objects.count(), 0)

    def test_staff_missing_permission(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "maintenanceMode": True,
        }

        non_staff_user = UserFactory.create(is_staff=True, user_permissions=tuple())
        self.client.force_login(non_staff_user)
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Form.objects.count(), 0)

    def test_anonymous_user(self):
        url = reverse(
            "api:v3:form-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "maintenanceMode": True,
        }

        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Form.objects.count(), 0)
