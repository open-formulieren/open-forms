import copy
import uuid
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Permission
from django.test import override_settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from digid_eherkenning.choices import DigiDAssuranceLevels
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.config.models import GlobalConfiguration
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory

from ..api.serializers import FormSerializer
from ..constants import StatementCheckboxChoices
from ..models import Form
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


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

    def test_list_anon(self):
        self.client.logout()

        FormFactory.create_batch(2)
        FormFactory.create(active=False)
        FormFactory.create(deleted_=True)

        url = reverse("api:form-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_staff(self):
        FormFactory.create_batch(2)
        FormFactory.create(active=False)
        FormFactory.create(deleted_=True)

        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_non_staff_with_permission(self):
        FormFactory.create_batch(2)
        FormFactory.create(active=False)
        FormFactory.create(deleted_=True)

        self.user.user_permissions.add(Permission.objects.get(codename="view_form"))
        self.user.is_staff = False
        self.user.save()

        url = reverse("api:form-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # two forms are hidden
        self.assertEqual(len(response.json()), 2)

    def test_list_staff_with_permission(self):
        FormFactory.create_batch(2)
        FormFactory.create(active=False)
        FormFactory.create(deleted_=True)

        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # show all forms excl deleted
        self.assertEqual(len(response.json()), 3)

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

    def test_create_form_successful(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "auth_backends": [
                {
                    "backend": "digid",
                }
            ],
            "internal_remarks": "Remark 1",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.assertEqual(form.name, "Test Post Form")
        self.assertEqual(form.slug, "test-post-form")
        self.assertEqual(form.internal_remarks, "Remark 1")

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_create_form_unsuccessful_with_bad_data(self, _mock):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "bad": "data",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Form.objects.exists())
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "name",
                        "code": "required",
                        "reason": _("This field is required."),
                    },
                    {
                        "name": "slug",
                        "code": "required",
                        "reason": _("This field is required."),
                    },
                ],
            },
        )

    def test_create_form_unsuccessful_without_authorization(self):
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Form.objects.exists())

    def test_partial_update_of_form(self):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "name": "Test Patch Form",
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.name, "Test Patch Form")

    def test_partial_update_of_form_unsuccessful_without_authorization(self):
        form = FormFactory.create()
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "name": "Test Patch Form",
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # as staff
        self.user.is_staff = True
        self.user.save()

        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_of_form_unsuccessful_when_form_cannot_be_found(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": uuid.uuid4()})
        data = {
            "name": "Test Patch Form",
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_complete_update_of_form_successful(self):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "name": "Test Put Form",
            "slug": "test-put-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.name, "Test Put Form")
        self.assertEqual(form.slug, "test-put-form")

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

    def test_create_form_in_maintenance_mode_successful(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "maintenanceMode": True,
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.assertEqual(form.name, "Test Post Form")
        self.assertEqual(form.slug, "test-post-form")
        self.assertEqual(form.maintenance_mode, True)

    def test_create_form_with_custom_texts_successful(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "literals": {
                "beginText": {"value": "Different Begin Text"},
                "previousText": {"value": "Different Previous Text"},
                "changeText": {"value": "Different Change Text"},
                "confirmText": {"value": "Different Confirm Text"},
            },
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.assertEqual(form.name, "Test Post Form")
        self.assertEqual(form.slug, "test-post-form")
        self.assertEqual(form.begin_text, "Different Begin Text")
        self.assertEqual(form.previous_text, "Different Previous Text")
        self.assertEqual(form.change_text, "Different Change Text")
        self.assertEqual(form.confirm_text, "Different Confirm Text")

    def test_updating_of_form_to_put_it_in_maintenance_mode(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "maintenanceMode": True,
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.maintenance_mode, True)

    def test_updating_of_form_texts_successful(self):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "literals": {
                "beginText": {"value": "Different Begin Text"},
                "previousText": {"value": "Different Previous Text"},
                "changeText": {"value": "Different Change Text"},
                "confirmText": {"value": "Different Confirm Text"},
            }
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.begin_text, "Different Begin Text")
        self.assertEqual(form.previous_text, "Different Previous Text")
        self.assertEqual(form.change_text, "Different Change Text")
        self.assertEqual(form.confirm_text, "Different Confirm Text")

    def test_updating_of_single_form_text_successful(self):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "literals": {
                "beginText": {"value": "Different Begin Text"},
            }
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.begin_text, "Different Begin Text")

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_complete_update_of_form_with_incomplete_data_unsuccessful(self, _mock):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "name": "Test Put Form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "slug",
                        "code": "required",
                        "reason": _("This field is required."),
                    }
                ],
            },
        )

    def test_complete_update_of_form_unsuccessful_without_authorization(self):
        form = FormFactory.create()
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Put Form")
        self.assertNotEqual(form.slug, "test-put-form")

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_complete_update_of_form_unsuccessful_with_bad_data(self, _mock):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "bad": "data",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "name",
                        "code": "required",
                        "reason": _("This field is required."),
                    },
                    {
                        "name": "slug",
                        "code": "required",
                        "reason": _("This field is required."),
                    },
                ],
            },
        )

    def test_complete_update_of_form_when_form_cannot_be_found(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": uuid.uuid4()})
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_form_with_confirmation_email_template_successful(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "confirmation_email_template": {
                "subject": "The subject",
                "content": "The content: {% appointment_information %} {% payment_information %} {% cosign_information %}",
            },
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.assertEqual(form.name, "Test Post Form")
        self.assertEqual(form.slug, "test-post-form")
        self.assertEqual(form.confirmation_email_template.subject, "The subject")
        self.assertEqual(
            form.confirmation_email_template.content,
            "The content: {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

    def test_creating_a_confirmation_email_template_for_an_existing_form(self):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "confirmation_email_template": {
                "subject": "The subject",
                "content": "The content {% appointment_information %} {% payment_information %} {% cosign_information %}",
            }
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.confirmation_email_template.subject, "The subject")
        self.assertEqual(
            form.confirmation_email_template.content,
            "The content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

    def test_creating_a_confirmation_email_fails_for_missing_template_tags(self):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "confirmation_email_template": {
                "subject": "The subject",
                "content": "The content {% appointment_information %} {% payment_information %} {% cosign_information %}",
            }
        }

        for missing_tag in [
            "{% appointment_information %}",
            "{% payment_information %}",
        ]:
            with self.subTest(missing_tag=missing_tag):
                modified_data = copy.deepcopy(data)
                modified_data["confirmation_email_template"]["content"] = modified_data[
                    "confirmation_email_template"
                ]["content"].replace(missing_tag, "")

                response = self.client.patch(url, data=modified_data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(
                    response.json()["invalidParams"][0]["reason"],
                    _("Missing required template-tag {tag}").format(tag=missing_tag),
                )

    def test_updating_a_confirmation_email_template(self):
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
        data = {
            "confirmation_email_template": {
                "subject": "Updated subject",
                "content": "Updated content: {% appointment_information %} {% payment_information %} {% cosign_information %}",
            }
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.confirmation_email_template.subject, "Updated subject")
        self.assertEqual(
            form.confirmation_email_template.content,
            "Updated content: {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

    def test_deleting_a_confirmation_email_template_through_the_api(self):
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
        data = {
            "confirmation_email_template": None,
        }

        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form.refresh_from_db()

        self.assertEqual(form.confirmation_email_template.content, "")
        self.assertEqual(form.confirmation_email_template.subject, "")

    def test_sending_empty_confirmation_email_template_removes_the_confirmation_email_template(
        self,
    ):
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
        data = {"confirmation_email_template": {"subject": "", "content": ""}}

        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form.refresh_from_db()

        self.assertEqual(form.confirmation_email_template.content, "")
        self.assertEqual(form.confirmation_email_template.subject, "")

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

    def test_submission_confirmation_template_invalid_template(self):
        """
        Test 1064 regression: invalid template code was accepted.
        """
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        data = {
            "submission_confirmation_template": "yo {% invalid_tag %}",
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()["invalidParams"][0]
        self.assertEqual(error["name"], "submissionConfirmationTemplate")
        self.assertEqual(error["code"], "syntax_error")

    def test_create_form_with_brp_personen_request_options_successful(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "brp_personen_request_options": {
                "brp_personen_purpose_limitation_header_value": "BRPACT-AanschrijvenZakelijkGerechtigde",
                "brp_personen_processing_header_value": "Financiële administratie@Correspondentie factuur",
            },
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.assertEqual(form.name, "Test Post Form")
        self.assertEqual(form.slug, "test-post-form")
        self.assertEqual(
            form.brp_personen_request_options.brp_personen_purpose_limitation_header_value,
            "BRPACT-AanschrijvenZakelijkGerechtigde",
        )
        self.assertEqual(
            form.brp_personen_request_options.brp_personen_processing_header_value,
            "Financiële administratie@Correspondentie factuur",
        )

    def test_creating_a_brp_personen_request_options_for_an_existing_form(self):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "brp_personen_request_options": {
                "brp_personen_purpose_limitation_header_value": "BRPACT-AanschrijvenZakelijkGerechtigde",
                "brp_personen_processing_header_value": "Financiële administratie@Correspondentie factuur",
            },
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(
            form.brp_personen_request_options.brp_personen_purpose_limitation_header_value,
            "BRPACT-AanschrijvenZakelijkGerechtigde",
        )
        self.assertEqual(
            form.brp_personen_request_options.brp_personen_processing_header_value,
            "Financiële administratie@Correspondentie factuur",
        )

    def test_create_form_auto_login_authentication_backend_validation_fails(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-list")
        data = {
            "name": "Test Put Form",
            "slug": "test-put-form",
            "auth_backends": [
                {
                    "backend": "digid",
                }
            ],
            "auto_login_authentication_backend": "eherkenning",
        }

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = response.json()["invalidParams"][0]

        self.assertEqual(error["name"], "autoLoginAuthenticationBackend")
        self.assertEqual(error["code"], "invalid")

    def test_update_form_auto_login_authentication_backend_validation_fails(self):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "name": "Test Put Form",
            "slug": "test-put-form",
            "auth_backends": [
                {
                    "backend": "digid",
                }
            ],
            "auto_login_authentication_backend": "eherkenning",
        }

        for verb in ["put", "patch"]:
            with self.subTest(verb=verb):
                response = getattr(self.client, verb)(url, data=data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

                error = response.json()["invalidParams"][0]

                self.assertEqual(error["name"], "autoLoginAuthenticationBackend")
                self.assertEqual(error["code"], "invalid")

    def test_partial_update_form_auto_login_authentication_backend_validation_fails(
        self,
    ):
        """
        When altering `auth_backends` on an existing form that has a
        `auto_login_authentication_backend` configured, validation should check whether
        this auto login backend is still allowed
        """
        form = FormFactory.create(
            authentication_backend="digid", auto_login_authentication_backend="digid"
        )
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "auth_backends": [
                {
                    "backend": "eherkenning",
                }
            ],
        }

        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = response.json()["invalidParams"][0]

        self.assertEqual(error["name"], "autoLoginAuthenticationBackend")
        self.assertEqual(error["code"], "invalid")

    def test_create_form_auto_login_authentication_backend_validation_succeeds(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-list")
        data = {
            "name": "Test Put Form",
            "slug": "test-put-form",
            "auth_backends": [
                {
                    "backend": "eherkenning",
                },
                {
                    "backend": "digid",
                },
            ],
            "auto_login_authentication_backend": "digid",
        }

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_form_auto_login_authentication_backend_validation_succeeds(self):
        form = FormFactory.create()
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "name": "Test Put Form",
            "slug": "test-put-form",
            "auth_backends": [
                {
                    "backend": "eherkenning",
                },
                {
                    "backend": "digid",
                },
            ],
            "auto_login_authentication_backend": "digid",
        }

        for verb in ["put", "patch"]:
            with self.subTest(verb=verb):
                response = getattr(self.client, verb)(url, data=data)

                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_form_with_valid_authentication_backend_loa_choice_succeeds(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-list")
        data = {
            "name": "Test Form",
            "slug": "test-form",
            "auth_backends": [
                {
                    "backend": "digid",
                    "options": {
                        "loa": DigiDAssuranceLevels.middle,
                    },
                }
            ],
        }

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()["authBackends"][0]

        self.assertEqual(data["backend"], "digid")
        self.assertEqual(data["options"], {"loa": DigiDAssuranceLevels.middle})

    def test_create_form_with_invalid_authentication_backend_loa_choice_fails(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-list")
        data = {
            "name": "Test Form",
            "slug": "test-form",
            "auth_backends": [
                {
                    "backend": "digid",
                    "options": {
                        "loa": "whatever",
                    },
                }
            ],
        }

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = response.json()["invalidParams"][0]

        self.assertEqual(error["name"], "authBackends.0.options.loa")
        self.assertEqual(error["code"], "invalid_choice")

    def test_create_form_with_unknown_authentication_backend_attribute_succeeds_with_only_allowed_attributes(
        self,
    ):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-list")
        data = {
            "name": "Test Form",
            "slug": "test-form",
            "auth_backends": [
                {
                    "backend": "digid",
                    "options": {
                        "loa": DigiDAssuranceLevels.middle,
                        "some_unknown_attribute": "should be removed",
                    },
                }
            ],
        }

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()["authBackends"][0]

        self.assertEqual(data["backend"], "digid")
        self.assertEqual(data["options"], {"loa": DigiDAssuranceLevels.middle})


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

    def test_detail_shows_translated_values_based_on_request_header(self):
        with translation.override("en"):
            form = FormFactory.create(
                translation_enabled=True,
                begin_text="start",
                previous_text="prev",
                change_text="change",
                confirm_text="confirm",
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

    def test_create_with_translations(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "auth_backends": [
                {
                    "backend": "digid",
                }
            ],
            "translations": {
                "en": {
                    "name": "Form 1",
                    "begin_text": "start",
                    "change_text": "change",
                    "confirm_text": "confirm",
                    "previous_text": "prev",
                    "explanation_template": "explanation",
                    "submission_confirmation_template": "submission",
                },
                "nl": {
                    "name": "Formulier 1",
                    "begin_text": "begin",
                    "change_text": "pas aan",
                    "confirm_text": "bevestig",
                    "previous_text": "vorige",
                    "explanation_template": "uitleg",
                    "submission_confirmation_template": "bevestiging",
                },
            },
            "confirmation_email_template": {
                "subject": "foo",
                "content": "{% appointment_information %} {% payment_information %} {% cosign_information %}",
                "translations": {
                    "en": {
                        "subject": "Subject",
                        "content": "Content {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                    "nl": {
                        "subject": "Onderwerp",
                        "content": "Inhoud {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                },
            },
        }

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        form = Form.objects.get(uuid=response.data["uuid"])

        self.assertEqual(form.begin_text_en, "start")
        self.assertEqual(form.change_text_en, "change")
        self.assertEqual(form.confirm_text_en, "confirm")
        self.assertEqual(form.explanation_template_en, "explanation")
        self.assertEqual(form.name_en, "Form 1")
        self.assertEqual(form.previous_text_en, "prev")
        self.assertEqual(form.submission_confirmation_template_en, "submission")

        self.assertEqual(form.begin_text_nl, "begin")
        self.assertEqual(form.change_text_nl, "pas aan")
        self.assertEqual(form.confirm_text_nl, "bevestig")
        self.assertEqual(form.explanation_template_nl, "uitleg")
        self.assertEqual(form.name_nl, "Formulier 1")
        self.assertEqual(form.previous_text_nl, "vorige")
        self.assertEqual(form.submission_confirmation_template_nl, "bevestiging")

        self.assertEqual(form.confirmation_email_template.subject_en, "Subject")
        self.assertEqual(
            form.confirmation_email_template.content_en,
            "Content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

        self.assertEqual(form.confirmation_email_template.subject_nl, "Onderwerp")
        self.assertEqual(
            form.confirmation_email_template.content_nl,
            "Inhoud {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

    def test_update_with_translations(self):
        self.client.force_authenticate(user=self.user)

        form = FormFactory.create()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "translations": {
                "en": {
                    "begin_text": "start",
                    "change_text": "change",
                    "confirm_text": "confirm",
                    "name": "Form 1",
                    "previous_text": "prev",
                },
                "nl": {
                    "begin_text": "begin",
                    "change_text": "pas aan",
                    "confirm_text": "bevestig",
                    "name": "Formulier 1",
                    "previous_text": "vorige",
                },
            },
            "confirmation_email_template": {
                "subject": "foo",
                "content": "{% appointment_information %} {% payment_information %} {% cosign_information %}",
                "translations": {
                    "en": {
                        "subject": "Subject",
                        "content": "Content {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                    "nl": {
                        "subject": "Onderwerp",
                        "content": "Inhoud {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                },
            },
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form.refresh_from_db()

        self.assertEqual(form.begin_text_en, "start")
        self.assertEqual(form.change_text_en, "change")
        self.assertEqual(form.confirm_text_en, "confirm")
        self.assertEqual(form.explanation_template_en, "")
        self.assertEqual(form.name_en, "Form 1")
        self.assertEqual(form.previous_text_en, "prev")
        self.assertEqual(form.submission_confirmation_template_en, "")

        self.assertEqual(form.begin_text_nl, "begin")
        self.assertEqual(form.change_text_nl, "pas aan")
        self.assertEqual(form.confirm_text_nl, "bevestig")
        self.assertEqual(form.explanation_template_nl, "")
        self.assertEqual(form.name_nl, "Formulier 1")
        self.assertEqual(form.previous_text_nl, "vorige")
        self.assertEqual(form.submission_confirmation_template_nl, "")

        self.assertEqual(form.confirmation_email_template.subject_en, "Subject")
        self.assertEqual(
            form.confirmation_email_template.content_en,
            "Content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

        self.assertEqual(form.confirmation_email_template.subject_nl, "Onderwerp")
        self.assertEqual(
            form.confirmation_email_template.content_nl,
            "Inhoud {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

    def test_update_with_translations_confirmation_email_template_validate_content(
        self,
    ):
        self.client.force_authenticate(user=self.user)

        form = FormFactory.create()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "confirmation_email_template": {
                "subject": "foo",
                "content": "{% appointment_information %} {% payment_information %} {% cosign_information %}",
                "translations": {
                    "en": {
                        "subject": "Subject",
                        "content": "Content",
                    },
                    "nl": {
                        "subject": "Onderwerp",
                        "content": "Inhoud {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                },
            },
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_params = response.json()["invalidParams"]
        self.assertEqual(
            invalid_params,
            [
                {
                    "name": "confirmationEmailTemplate.translations.en.content",
                    "code": "invalid",
                    "reason": _("Missing required template-tag {tag}").format(
                        tag="{% appointment_information %}"
                    ),
                }
            ],
        )

    def test_update_with_translations_validate_literals(self):
        self.client.force_authenticate(user=self.user)

        form = FormFactory.create()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "translations": {
                "en": {
                    "name": "x" * 151,
                    "explanation_template": "",
                    "submission_confirmation_template": r"{{}}}",
                    "begin_text": {"value": "incorrect_value"},
                    "change_text": {"value": "incorrect_value"},
                    "confirm_text": {"value": "incorrect_value"},
                    "previous_text": {"value": "incorrect_value"},
                },
                "nl": {
                    "name": "x" * 151,
                    "explanation_template": "",
                    "submission_confirmation_template": r"{{}}}",
                    "begin_text": "correct",
                    "change_text": {"value": "incorrect_value"},
                    "confirm_text": {"value": "incorrect_value"},
                    "previous_text": "x" * 51,
                },
            },
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_params = response.json()["invalidParams"]
        expected_errors = [
            {
                "name": "translations.nl.name",
                "code": "max_length",
                "reason": _(
                    "Ensure this field has no more than {max_length} characters."
                ).format(max_length=150),
            },
            {
                "name": "translations.nl.changeText",
                "code": "invalid",
                "reason": _("Not a valid string."),
            },
            {
                "name": "translations.nl.confirmText",
                "code": "invalid",
                "reason": _("Not a valid string."),
            },
            {
                "name": "translations.nl.previousText",
                "code": "max_length",
                "reason": _(
                    "Ensure this field has no more than {max_length} characters."
                ).format(max_length=50),
            },
            {
                "name": "translations.nl.submissionConfirmationTemplate",
                "code": "syntax_error",
                "reason": "Empty variable tag on line 1",
            },
            {
                "name": "translations.en.name",
                "code": "max_length",
                "reason": _(
                    "Ensure this field has no more than {max_length} characters."
                ).format(max_length=150),
            },
            {
                "name": "translations.en.submissionConfirmationTemplate",
                "code": "syntax_error",
                "reason": "Empty variable tag on line 1",
            },
            {
                "name": "translations.en.beginText",
                "code": "invalid",
                "reason": _("Not a valid string."),
            },
            {
                "name": "translations.en.changeText",
                "code": "invalid",
                "reason": _("Not a valid string."),
            },
            {
                "name": "translations.en.confirmText",
                "code": "invalid",
                "reason": _("Not a valid string."),
            },
            {
                "name": "translations.en.previousText",
                "code": "invalid",
                "reason": _("Not a valid string."),
            },
        ]

        for error in expected_errors:
            with self.subTest(field=error["name"], code=error["code"]):
                self.assertIn(error, invalid_params)

        expected_valid = [
            "translations.en.explanation_template",
            "translations.nl.explanation_template",
            "translations.nl.begin_text",
        ]
        error_names = [err["name"] for err in invalid_params]
        for unexpected_error in expected_valid:
            with self.subTest(name=unexpected_error):
                self.assertNotIn(unexpected_error, error_names)

    def test_create_with_translations_normalize_values(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "auth_backends": [
                {
                    "backend": "digid",
                }
            ],
            "translations": {
                "en": {
                    "begin_text": "start",
                    "change_text": "change",
                    "confirm_text": "confirm",
                },
                "nl": {
                    "explanation_template": "uitleg",
                    "name": "Formulier 1",
                    "previous_text": "vorige",
                    "submission_confirmation_template": "bevestiging",
                },
            },
            "confirmation_email_template": {
                "subject": "foo",
                "content": "{% appointment_information %} {% payment_information %} {% cosign_information %}",
                "translations": {
                    "en": {
                        "subject": "Subject",
                        "content": "Content {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                },
            },
        }

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        form = Form.objects.get(uuid=response.data["uuid"])

        self.assertEqual(form.begin_text_en, "start")
        self.assertEqual(form.change_text_en, "change")
        self.assertEqual(form.confirm_text_en, "confirm")
        self.assertEqual(form.explanation_template_en, "")
        self.assertEqual(form.name_en, "")
        self.assertEqual(form.previous_text_en, "")
        self.assertEqual(form.submission_confirmation_template_en, "")

        self.assertEqual(form.begin_text_nl, "")
        self.assertEqual(form.change_text_nl, "")
        self.assertEqual(form.confirm_text_nl, "")
        self.assertEqual(form.explanation_template_nl, "uitleg")
        self.assertEqual(form.name_nl, "Formulier 1")
        self.assertEqual(form.previous_text_nl, "vorige")
        self.assertEqual(form.submission_confirmation_template_nl, "bevestiging")

        self.assertEqual(form.confirmation_email_template.subject_en, "Subject")
        self.assertEqual(
            form.confirmation_email_template.content_en,
            "Content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

        # checks that the fallback to original non-translation fields is registered
        # in the default language field
        self.assertEqual(form.confirmation_email_template.subject_nl, "foo")
        self.assertEqual(
            form.confirmation_email_template.content_nl,
            "{% appointment_information %} {% payment_information %} {% cosign_information %}",
        )
