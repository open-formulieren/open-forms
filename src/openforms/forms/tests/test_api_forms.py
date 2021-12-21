import copy
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    TokenFactory,
    UserFactory,
)
from openforms.config.models import GlobalConfiguration
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.tests.utils import NOOP_CACHES

from ..constants import ConfirmationEmailOptions
from ..models import Form, FormDefinition, FormStep
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


class FormsAPITests(APITestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory.create()
        self.client.force_authenticate(user=self.user)

    def test_list(self):
        FormFactory.create_batch(2)
        FormFactory.create(active=False)
        FormFactory.create(deleted_=True)

        url = reverse("api:form-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_staff(self):
        FormFactory.create_batch(2)
        FormFactory.create(active=False)
        FormFactory.create(deleted_=True)

        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

    def test_non_staff_cant_access_deleted_form(self):
        form = FormFactory.create(deleted_=True)

        response = self.client.get(
            reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_form_by_uuid(self):
        form = FormFactory.create()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["uuid"], str(form.uuid))

    def test_retrieve_form_by_slug(self):
        form = FormFactory.create()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.slug})

        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["slug"], form.slug)

    def test_retrieve_inactive_staff(self):
        form = FormFactory.create(active=False)

        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_retrieve_inactive_anon(self):
        form = FormFactory.create(active=False)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_not_retrieve_deleted(self):
        form = FormFactory.create(deleted_=True)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_form_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "authentication_backends": ["digid"],
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.assertEqual(form.name, "Test Post Form")
        self.assertEqual(form.slug, "test-post-form")

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_create_form_unsuccessful_with_bad_data(self, _mock):
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
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Patch Form")

    def test_partial_update_of_form_unsuccessful_when_form_cannot_be_found(self):
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
        self.user.is_staff = True
        self.user.save()

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
                "instance": f"urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
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
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "confirmation_email_template": {
                "subject": "The subject",
                "content": "The content: {% appointment_information %} {% payment_information %}",
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
            "The content: {% appointment_information %} {% payment_information %}",
        )

    def test_creating_a_confirmation_email_template_for_an_existing_form(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "confirmation_email_template": {
                "subject": "The subject",
                "content": "The content {% appointment_information %} {% payment_information %}",
            }
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.confirmation_email_template.subject, "The subject")
        self.assertEqual(
            form.confirmation_email_template.content,
            "The content {% appointment_information %} {% payment_information %}",
        )

    def test_creating_a_confirmation_email_fails_for_missing_template_tags(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "confirmation_email_template": {
                "subject": "The subject",
                "content": "The content {% appointment_information %} {% payment_information %}",
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
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {
            "confirmation_email_template": {
                "subject": "Updated subject",
                "content": "Updated content: {% appointment_information %} {% payment_information %}",
            }
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.confirmation_email_template.subject, "Updated subject")
        self.assertEqual(
            form.confirmation_email_template.content,
            "Updated content: {% appointment_information %} {% payment_information %}",
        )

    def test_deleting_a_confirmation_email_template_through_the_api(self):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Initial subject",
            content="Initial content",
        )
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {"confirmation_email_template": None}

        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertFalse(form.confirmation_email_template.is_usable)

    def test_sending_empty_confirmation_email_template_removes_the_confirmation_email_template(
        self,
    ):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Initial subject",
            content="Initial content",
            update_form_confirmation_email_option=False,
        )
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        data = {"confirmation_email_template": {"subject": "", "content": ""}}

        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertFalse(form.confirmation_email_template.is_usable)

    def test_sending_partial_confirmation_email_template_raises_an_exception(
        self,
    ):
        patcher = patch(
            "openforms.utils.validators.DjangoTemplateValidator.check_required_tags",
            return_value=None,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        template = ConfirmationEmailTemplateFactory.create(
            subject="Initial subject",
            content="Initial content",
        )
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": template.form.uuid})
        data_to_test = [
            {
                "confirmation_email_template": {
                    "subject": "Updated subject",
                }
            },
            {"confirmation_email_template": {"subject": "", "content": "The content"}},
        ]

        for data in data_to_test:
            with self.subTest(data=data):

                response = self.client.patch(url, data=data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(
                    response.json()["invalidParams"][0]["reason"],
                    _(
                        "The fields {fields} must all be provided if one of them is provided."
                    ).format(fields="subject, content"),
                )

    def test_getting_a_form_with_a_confirmation_email_template(self):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Initial subject",
            content="Initial content",
        )
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["confirmationEmailTemplate"],
            {"subject": "Initial subject", "content": "Initial content"},
        )

    def test_configure_form_use_form_template_but_not_usable(self):
        """
        Assert that it's not possible to configure a form to use an unusable confirmation
        email template.

        Unusable is defined as having an empty subject or content.
        """
        user = StaffUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create()
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        invalid_templates = [
            None,
            {"subject": "", "content": ""},
        ]

        for invalid_template in invalid_templates:
            with self.subTest(invalid_template_data=invalid_template):
                data = {
                    "confirmation_email_template": invalid_template,
                    "confirmation_email_option": ConfirmationEmailOptions.form_specific_email,
                }

                response = self.client.patch(url, data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                err_message = response.json()["invalidParams"][0]["reason"]
                self.assertEqual(
                    err_message,
                    _(
                        "The form specific confirmation email template is not set up correctly and "
                        "can therefore not be selected."
                    ),
                )

    def test_submission_confirmation_template_invalid_template(self):
        """
        Test 1064 regression: invalid template code was accepted.
        """
        user = StaffUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create()
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        data = {
            "submission_confirmation_template": "yo {% invalid_tag %}",
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()["invalidParams"][0]
        self.assertEqual(error["name"], "submissionConfirmationTemplate")
        self.assertEqual(error["code"], "syntax_error")


class CopyFormAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john", password="secret", email="john@example.com"
        )
        self.token = TokenFactory(user=self.user)

    @override_settings(CACHES=NOOP_CACHES)
    def test_form_copy(self):
        self.user.is_staff = True
        self.user.save()

        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        url = reverse("api:form-copy", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        copied_form = Form.objects.last()
        copied_form_step = copied_form.formstep_set.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(response.json()["uuid"], str(copied_form.uuid))
        self.assertEqual(response.json()["name"], copied_form.name)
        self.assertEqual(response.json()["loginRequired"], copied_form.login_required)
        self.assertEqual(response.json()["product"], copied_form.product)
        self.assertEqual(response.json()["slug"], copied_form.slug)
        self.assertEqual(
            response.json()["steps"][0]["uuid"], str(copied_form_step.uuid)
        )
        self.assertEqual(
            response.json()["steps"][0]["formDefinition"],
            copied_form_step.form_definition.name,
        )

        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 1)
        self.assertEqual(FormStep.objects.count(), 2)

        self.assertIn(
            reverse("api:form-detail", kwargs={"uuid_or_slug": copied_form.uuid}),
            response["Location"],
        )

        self.assertNotEqual(copied_form.pk, form.pk)
        self.assertNotEqual(copied_form.uuid, str(form.uuid))
        self.assertEqual(copied_form.active, form.active)
        self.assertEqual(copied_form.registration_backend, form.registration_backend)
        self.assertEqual(copied_form.name, _("{name} (copy)").format(name=form.name))
        self.assertIsNone(copied_form.product)
        self.assertEqual(copied_form.slug, _("{slug}-copy").format(slug=form.slug))

        self.assertNotEqual(copied_form_step.pk, form_step.pk)
        self.assertNotEqual(copied_form_step.uuid, str(form_step.uuid))
        self.assertEqual(copied_form_step.form.pk, copied_form.pk)
        self.assertEqual(copied_form_step.optional, form_step.optional)
        self.assertEqual(copied_form_step.order, form_step.order)

    def test_form_copy_already_exists(self):
        self.user.is_staff = True
        self.user.save()

        form = FormFactory.create()

        url = reverse("api:form-copy", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(
            response.json()["name"], _("{name} (copy)").format(name=form.name)
        )
        self.assertEqual(
            response.json()["slug"], _("{slug}-copy").format(slug=form.slug)
        )

        copy_form_slug = response.json()["slug"]

        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(
            response.json()["name"], _("{name} (copy)").format(name=form.name)
        )
        self.assertEqual(response.json()["slug"], "{}-2".format(copy_form_slug))

        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(
            response.json()["name"], _("{name} (copy)").format(name=form.name)
        )
        self.assertEqual(response.json()["slug"], "{}-3".format(copy_form_slug))

    def test_form_copy_token_auth_required(self):
        form = FormFactory.create()
        url = reverse("api:form-copy", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_copy_session_auth_not_allowed(self):
        self.user.is_staff = True
        self.user.save()

        self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

        form = FormFactory.create()
        url = reverse("api:form-copy", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_copy_staff_required(self):
        self.user.is_staff = False
        self.user.save()

        form = FormFactory.create()
        url = reverse("api:form-copy", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.post(
            url,
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
