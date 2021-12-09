import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import TokenFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..models import FormStep
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


class FormsStepsAPITests(APITestCase):
    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john", password="secret", email="john@example.com"
        )
        self.step = FormStepFactory.create()
        self.other_form_definition = FormDefinitionFactory.create()

        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        assert self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

    def test_steps_list(self):
        url = reverse(
            "api:form-steps-list", kwargs={"form_uuid_or_slug": self.step.form.uuid}
        )
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_form_step_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-list", kwargs={"form_uuid_or_slug": self.step.form.uuid}
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}", "index": 0}
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )

    def test_create_form_step_successful_with_custom_button_text(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-list", kwargs={"form_uuid_or_slug": self.step.form.uuid}
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {
            "formDefinition": f"http://testserver{form_detail_url}",
            "index": 0,
            "literals": {
                "previousText": {"value": "Different Previous Text"},
                "saveText": {"value": "Different Save Text"},
                "nextText": {"value": "Different Next Text"},
            },
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )
        form_step = FormStep.objects.get(form_definition=self.other_form_definition)
        self.assertEqual(form_step.previous_text, "Different Previous Text")
        self.assertEqual(form_step.save_text, "Different Save Text")
        self.assertEqual(form_step.next_text, "Different Next Text")

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_create_form_step_unsuccessful_with_bad_data(self, _mock):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-list", kwargs={"form_uuid_or_slug": self.step.form.uuid}
        )
        data = {
            "bad": "data",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(FormStep.objects.count(), 1)
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
                        "name": "index",
                        "code": "required",
                        "reason": _("This field is required."),
                    },
                    {
                        "name": "formDefinition",
                        "code": "required",
                        "reason": _("This field is required."),
                    },
                ],
            },
        )

    def test_create_form_step_unsuccessful_when_form_is_not_found(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-steps-list", kwargs={"form_uuid_or_slug": uuid.uuid4()})
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.step.form_definition.uuid}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(FormStep.objects.count(), 1)

    def test_create_form_step_unsuccessful_without_authorization(self):
        url = reverse(
            "api:form-steps-list", kwargs={"form_uuid_or_slug": self.step.form.uuid}
        )
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.step.form_definition.uuid}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(FormStep.objects.count(), 1)

    def test_complete_form_step_update_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}", "index": 0}
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )

    def test_complete_form_step_update_with_custom_texts_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {
            "formDefinition": f"http://testserver{form_detail_url}",
            "index": 0,
            "literals": {
                "previousText": {"value": "Different Previous Text"},
                "saveText": {"value": "Different Save Text"},
                "nextText": {"value": "Different Next Text"},
            },
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )
        form_step = FormStep.objects.get(form_definition=self.other_form_definition)
        self.assertEqual(form_step.previous_text, "Different Previous Text")
        self.assertEqual(form_step.save_text, "Different Save Text")
        self.assertEqual(form_step.next_text, "Different Next Text")

    def test_complete_form_step_update_unsuccessful_when_form_step_not_found(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": uuid.uuid4()},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_complete_form_step_update_unsuccessful_with_non_existant_form_definition(
        self, _mock
    ):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": uuid.uuid4()},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}", "index": 0}
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )
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
                        "name": "formDefinition",
                        "code": "does_not_exist",
                        "reason": _("Invalid hyperlink - Object does not exist."),
                    }
                ],
            },
        )

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_complete_form_step_update_unsuccessful_with_bad_data(self, _mock):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        data = {
            "bad": "data",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(FormStep.objects.count(), 1)
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
                        "name": "index",
                        "code": "required",
                        "reason": _("This field is required."),
                    },
                    {
                        "name": "formDefinition",
                        "code": "required",
                        "reason": _("This field is required."),
                    },
                ],
            },
        )

    def test_complete_form_step_update_unsuccessful_without_authorization(self):
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.step.form_definition.uuid}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )

    def test_partial_form_step_update_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )

    def test_partial_form_step_update_with_texts_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {
            "formDefinition": f"http://testserver{form_detail_url}",
            "literals": {
                "previousText": {"value": "Different Previous Text"},
                "saveText": {"value": "Different Save Text"},
                "nextText": {"value": "Different Next Text"},
            },
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )
        form_step = FormStep.objects.get(form_definition=self.other_form_definition)
        self.assertEqual(form_step.previous_text, "Different Previous Text")
        self.assertEqual(form_step.save_text, "Different Save Text")
        self.assertEqual(form_step.next_text, "Different Next Text")

    def test_partial_form_step_update_with_of_single_text_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {
            "formDefinition": f"http://testserver{form_detail_url}",
            "literals": {
                "previousText": {"value": "Different Previous Text"},
            },
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )
        form_step = FormStep.objects.get(form_definition=self.other_form_definition)
        self.assertEqual(form_step.previous_text, "Different Previous Text")

    def test_partial_form_step_update_unsuccessful_when_form_step_not_found(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": uuid.uuid4()},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": uuid.uuid4()}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_partial_form_step_update_unsuccessful_when_form_definition_not_found(
        self, _mock
    ):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": uuid.uuid4()}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )
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
                        "name": "formDefinition",
                        "code": "does_not_exist",
                        "reason": _("Invalid hyperlink - Object does not exist."),
                    }
                ],
            },
        )

    def test_partial_form_step_update_unsuccessful_without_authorization(self):
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.step.form_definition.uuid}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )

    def test_delete_form_step_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FormStep.objects.exists())

    def test_delete_form_step_unsuccessful_when_form_not_found(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": uuid.uuid4()},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(FormStep.objects.count(), 1)

    def test_delete_form_step_unsuccessful_when_not_authorized(self):
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": self.step.form.uuid, "uuid": self.step.uuid},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(FormStep.objects.count(), 1)

    def test_form_delete(self):
        self.user.is_staff = True
        self.user.save()
        token = TokenFactory(user=self.user)

        form = FormFactory.create()
        submission = SubmissionFactory.create(form=form)

        response = self.client.delete(
            reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        form.refresh_from_db()
        self.assertTrue(form._is_deleted)

        response = self.client.get(
            reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
        )

        # The form is still visible for staff users (Needed for the CRUD admin page)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Submission still exists
        submission.refresh_from_db()
        self.assertEqual(submission.form, form)

    def test_form_delete_staff_required(self):
        token = TokenFactory(user=self.user)

        form = FormFactory.create()

        response = self.client.delete(
            reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        form.refresh_from_db()
        self.assertFalse(form._is_deleted)

        response = self.client.get(
            reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_form_delete_token_required(self):
        form = FormFactory.create()

        response = self.client.delete(
            reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        form.refresh_from_db()
        self.assertFalse(form._is_deleted)

        response = self.client.get(
            reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
