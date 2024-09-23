"""
Tests for the start of a submission.

A submission acts sort of like a session. It is tied to a particular form (which is made
up of form steps with their definitions).

Functional requirements are:

* multiple submissions for the same flow must be able to exist at the same time
* data of different submissions should not affect each other
* "login" usually is not releavnt, as we mostly deal with anonymous users. However,
  some plugins/functionality is limited to staff users.

See ``test_disabled_forms.py`` for more extensive tests around maintenance mode.
"""

from pathlib import Path
from unittest.mock import patch

from django.test import override_settings, tag

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.authentication.service import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import (
    FormFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ..constants import SUBMISSIONS_SESSION_KEY, SubmissionValueVariableSources
from ..models import Submission, SubmissionValueVariable

TEST_FILES = (Path(__file__).parent / "data").resolve()


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class SubmissionStartTests(OFVCRMixin, APITestCase):
    VCR_TEST_FILES = TEST_FILES
    endpoint = reverse_lazy("api:submission-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # ensure there is a form definition
        cls.form = FormFactory.create()
        cls.step = FormStepFactory.create(form=cls.form)
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def test_start_submission(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body, HTTP_HOST="testserver.com")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get()

        response_json = response.json()
        expected = {
            "id": str(submission.uuid),
            "form": f"http://testserver.com{self.form_url}",
        }
        for key, value in expected.items():
            with self.subTest(key=key, value=value):
                self.assertIn(key, response_json)
                self.assertEqual(response_json[key], value)

        # check that the submission ID is in the session
        self.assertEqual(
            response.wsgi_request.session[SUBMISSIONS_SESSION_KEY],
            [str(submission.uuid)],
        )

    def test_start_second_submission(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        with self.subTest(state="first submission"):
            response = self.client.post(self.endpoint, body)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with self.subTest(state="second submission"):
            response = self.client.post(self.endpoint, body)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            submissions = Submission.objects.all()
            self.assertEqual(submissions.count(), 2)

            ids = submissions.values_list("uuid", flat=True)
            self.assertEqual(
                set(response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]),
                {str(uuid) for uuid in ids},
            )

    def test_start_submission_bsn_in_session(self):
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
        }
        session.save()

        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get()
        self.assertEqual(submission.auth_info.value, "123456782")
        self.assertEqual(submission.auth_info.plugin, "digid")

        # Auth info should be removed from session after the submission is started
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)

    @tag("gh-4199")
    def test_two_submissions_within_same_session(self):
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
        }
        session.save()

        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get()
        self.assertEqual(submission.auth_info.value, "123456782")
        self.assertEqual(submission.auth_info.plugin, "digid")

        # Auth info should be removed from session after the submission is started
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)

        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
            "anonymous": True,
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        submission = Submission.objects.last()
        with self.assertRaises(Submission.auth_info.RelatedObjectDoesNotExist):
            submission.auth_info

    def test_start_submission_on_deleted_form(self):
        form = FormFactory.create(deleted_=True)
        FormStepFactory.create(form=form)

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_start_submission_blank_form_url(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_start_submission_bad_form_url(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://badserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("openforms.logging.logevent._create_log")
    def test_start_submission_with_prefill(self, mock_logevent):
        FormVariableFactory.create(
            form=self.form,
            form_definition=self.step.form_definition,
            prefill_plugin="demo",
            prefill_attribute="random_string",
        )
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body, HTTP_HOST="testserver.com")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        submission = Submission.objects.get()
        submission_variables = SubmissionValueVariable.objects.filter(
            submission=submission
        )

        self.assertEqual(1, submission_variables.count())

        prefilled_variable = submission_variables.get()

        self.assertTrue(prefilled_variable.value != "")
        self.assertEqual(
            SubmissionValueVariableSources.prefill, prefilled_variable.source
        )

    def test_start_submission_with_initial_data_reference(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
            "initialDataReference": "of-or-3452fre3",
        }

        response = self.client.post(self.endpoint, body)

        submission = Submission.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            submission.initial_data_reference, body["initialDataReference"]
        )

    def test_start_submission_with_initial_data_reference_and_anonymous_raises_error(
        self,
    ):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
            "initialDataReference": "of-or-3452fre3",
            "anonymous": True,
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json()["detail"], "Cannot pass data reference as anonymous user"
        )
        self.assertFalse(Submission.objects.exists())

    def test_start_submission_with_initial_data_reference_and_not_owner_of_object_raises_error(
        self,
    ):
        # objects_api_group_unused = ObjectsAPIGroupConfigFactory.create()
        objects_api_group_used = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        with get_objects_client(objects_api_group_used) as client:
            object = client.create_object(
                record_data=prepare_data_for_registration(
                    data={"bsn": "111222333", "foo": "bar"},
                    objecttype_version=1,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
            )

        object_ref = object["uuid"]

        # unused_objects_backend = FormRegistrationBackendFactory.create(
        #     form=self.form,
        #     backend="objects_api",
        #     options={
        #         "version": 2,
        #         "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
        #         "iot_attachment": "",
        #         "objects_api_group": objects_api_group_unused.pk,
        #         # TODO these are probably not needed?
        #         # "variables_mapping": [],
        #         # "iot_submission_csv": "",
        #         "objecttype_version": 1,
        #         # "geometry_variable_key": "",
        #         # "iot_submission_report": "",
        #         # "upload_submission_csv": False,
        #         # "update_existing_object": True,
        #     },
        # )
        objects_backend_incorrect_api_group = FormRegistrationBackendFactory.create(
            form=self.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": 5,
                "objecttype_version": 1,
            },
        )
        irrelevant_backend = FormRegistrationBackendFactory.create(
            form=self.form, backend="email"
        )
        objects_backend = FormRegistrationBackendFactory.create(
            form=self.form,
            backend="objects_api",
            options={
                "version": 2,
                "objecttype": "3edfdaf7-f469-470b-a391-bb7ea015bd6f",
                "objects_api_group": objects_api_group_used.pk,
                "objecttype_version": 1,
            },
        )

        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
        }
        session.save()

        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
            "initialDataReference": object_ref,
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json()["detail"], "User is not the owner of the referenced object"
        )
        self.assertFalse(Submission.objects.exists())

    def test_start_submission_with_initial_data_reference_and_no_backends_configured_raises_error(
        self,
    ):
        FormRegistrationBackendFactory.create(form=self.form, backend="email")

        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
        }
        session.save()

        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
            "initialDataReference": "of-or-3452fre3",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json()["detail"],
            "Could not fetch object from initial data reference",
        )
        self.assertFalse(Submission.objects.exists())
