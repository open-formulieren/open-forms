from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from digid_eherkenning.choices import DigiDAssuranceLevels
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
    def setUp(self):
        super().setUp()

        admin_user = UserFactory.create(
            is_staff=True, user_permissions=("forms.change_form",)
        )
        self.client.force_authenticate(user=admin_user)

    def test_create_minimal_form(self):
        url = reverse(
            "api:form-v3-detail",
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
            "api:form-v3-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "internal_name": "Create form internal",
            "internal_remarks": "This form is used for xyz",
            "translation_enabled": True,
            "auth_backends": [
                {
                    "backend": "demo",
                    "options": {"some_custom_attribute": "will be added"},
                },
                {
                    "backend": "digid",
                    "options": {"loa": DigiDAssuranceLevels.high},
                },
                {
                    "backend": "digid_oidc",
                    "options": {},
                },
            ],
            "auto_login_authentication_backend": "digid",
            "appointment_options": {
                "is_appointment": True,
            },
            "literals": {
                "beginText": {"value": "Different Begin Text"},
                "previousText": {"value": "Different Previous Text"},
                "changeText": {"value": "Different Change Text"},
                "confirmText": {"value": "Different Confirm Text"},
            },
            "product": reverse("api:product-detail", kwargs={"uuid": product.uuid}),
            "slug": "create-form",
            "category": reverse(
                "api:categories-detail", kwargs={"uuid": category.uuid}
            ),
            "theme": reverse("api:themes-detail", kwargs={"uuid": theme.uuid}),
            "show_progress_indicator": True,
            "show_summary_progress": True,
            "maintenanceMode": True,
            "active": True,
            "activate_on": activate_on.isoformat(),
            "deactivate_on": deactivate_on.isoformat(),
            "is_deleted": False,
            "submission_confirmation_template": "Have a cookie",
            "introduction_page_content": "You can ask for cookies here",
            "explanation_template": "Get ready to ask for some cookies",
            "submission_allowed": SubmissionAllowedChoices.yes,
            "submission_limit": 10,
            "submission_counter": 0,
            "suspension_allowed": True,
            "ask_privacy_consent": StatementCheckboxChoices.required,
            "ask_statement_of_truth": StatementCheckboxChoices.required,
            "submissions_removal_options": {
                "successful_submissions_removal_limit": 10,
                "successful_submissions_removal_method": RemovalMethods.delete_permanently,
                "incomplete_submissions_removal_limit": 5,
                "incomplete_submissions_removal_method": RemovalMethods.delete_permanently,
                "errored_submissions_removal_limit": 20,
                "errored_submissions_removal_method": RemovalMethods.delete_permanently,
                "all_submissions_removal_limit": 30,
            },
            "send_confirmation_email": True,
            "display_main_website_link": True,
            "include_confirmation_page_content_in_pdf": True,
            "translations": {
                "en": {
                    "name": "Create form",
                    "begin_text": "start",
                    "previous_text": "previous",
                    "change_text": "change",
                    "confirm_text": "confirm",
                    "submission_confirmation_template": "Have a cookie",
                    "introduction_page_content": "You can ask for cookies here",
                    "explanation_template": "Get ready to ask for some cookies",
                },
                "nl": {
                    "name": "Create formulier",
                    "begin_text": "start",
                    "previous_text": "vorige",
                    "change_text": "wijzigen",
                    "confirm_text": "bevestigen",
                    "submission_confirmation_template": "Neem een koekje",
                    "introduction_page_content": "Je kan hier voor koekjes vragen",
                    "explanation_template": "Wees klaar om voor koekjes te vragen",
                },
            },
            "brp_personen_request_options": {
                "brp_personen_purpose_limitation_header_value": "BRPACT-AanschrijvenZakelijkGerechtigde",
                "brp_personen_processing_header_value": "Financiële administratie@Correspondentie factuur",
            },
            "new_renderer_enabled": True,
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

        authentication_backends = form.auth_backends.all()
        demo_backend = authentication_backends.get(backend="demo")
        digid_backend = authentication_backends.get(backend="digid")
        digid_oidc_backend = authentication_backends.get(backend="digid_oidc")
        self.assertCountEqual(
            authentication_backends.values_list("backend", flat=True),
            ("demo", "digid", "digid_oidc"),
        )
        self.assertEqual(
            demo_backend.options,
            {"some_custom_attribute": "will be added"},
        )
        self.assertEqual(
            digid_backend.options,
            {"loa": DigiDAssuranceLevels.high},
        )
        self.assertEqual(digid_oidc_backend.options, {})

        self.assertEqual(form.auto_login_authentication_backend, "digid")
        self.assertTrue(form.is_appointment)
        self.assertEqual(form.product, product)
        self.assertEqual(form.slug, "create-form")
        self.assertEqual(form.category, category)
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

        # brp options
        brp_options = form.brp_personen_request_options
        self.assertEqual(
            brp_options.brp_personen_purpose_limitation_header_value,
            "BRPACT-AanschrijvenZakelijkGerechtigde",
        )
        self.assertEqual(
            brp_options.brp_personen_processing_header_value,
            "Financiële administratie@Correspondentie factuur",
        )

        self.assertTrue(form.new_renderer_enabled)

    def test_update_existing_form(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
        )

        url = reverse(
            "api:form-v3-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.name, "Update form")
        self.assertEqual(form.slug, "update-form")

    def test_deleted_form(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
            active=True,
            _is_deleted=True,
        )

        url = reverse(
            "api:form-v3-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.name, "Update form")
        self.assertEqual(form.slug, "update-form")

    def test_inactive_form(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
            active=False,
        )

        url = reverse(
            "api:form-v3-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.name, "Update form")
        self.assertEqual(form.slug, "update-form")

    def test_non_staff_user(self):
        url = reverse(
            "api:form-v3-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "maintenanceMode": True,
        }

        self.client.logout()
        non_staff_user = UserFactory.create(is_staff=False, user_permissions=tuple())
        self.client.force_login(non_staff_user)
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Form.objects.count(), 0)

    def test_staff_missing_permission(self):
        url = reverse(
            "api:form-v3-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "maintenanceMode": True,
        }

        self.client.logout()
        non_staff_user = UserFactory.create(is_staff=True, user_permissions=tuple())
        self.client.force_login(non_staff_user)
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Form.objects.count(), 0)

    def test_anonymous_user(self):
        url = reverse(
            "api:form-v3-detail",
            kwargs={"uuid": "559812e7-9bff-4142-ab41-0cc8cf4e5e32"},
        )
        data = {
            "name": "Create form",
            "slug": "create-form",
            "maintenanceMode": True,
        }

        self.client.logout()
        response = self.client.put(url, data=data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_data["code"], "not_authenticated")
        self.assertEqual(Form.objects.count(), 0)

    def test_unsupported_patch(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            name="Create form",
            slug="create-form",
        )

        url = reverse(
            "api:form-v3-detail",
            kwargs={"uuid": str(form.uuid)},
        )
        data = {
            "name": "Update form",
            "slug": "update-form",
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()

        self.assertEqual(form.name, "Create form")
        self.assertEqual(form.slug, "create-form")

    def test_unsupported_post(self):
        url = reverse(
            "api:form-v3-detail",
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
