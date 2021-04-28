"""
Test the registration hook on submissions.
"""
import uuid

from django.test import TestCase

from rest_framework import serializers
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from openforms.forms.models import Form
from openforms.submissions.tests.factories import SubmissionFactory

from ..registry import Registry
from ..submissions import register_submission
from .utils import patch_registry


class OptionsSerializer(serializers.Serializer):
    string = serializers.CharField()
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())


class ResultSerializer(serializers.Serializer):
    external_id = serializers.UUIDField()


class RegistrationHookTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = Service.objects.create(
            label="Test",
            api_type=APITypes.orc,
            auth_type=AuthTypes.no_auth,
        )

        cls.submission = SubmissionFactory.create(
            form__registration_backend="callback",
            form__registration_backend_options={
                "string": "some-option",
                "service": cls.service.id,
            },
        )

    def test_assertion_callback_with_deserialized_options(self):
        register = Registry()

        # register the callback, including the assertions
        @register(
            "callback",
            "Assertion callback",
            configuration_options=OptionsSerializer,
        )
        def callback(submission, options):
            self.assertEqual(submission, self.submission)
            self.assertIsInstance(options, dict)
            self.assertEqual(options["string"], "some-option")
            self.assertEqual(options["service"], self.service)

            return {"result": "ok"}

        # call the hook for the submission, while patching the model field registry
        model_field = Form._meta.get_field("registration_backend")
        with patch_registry(model_field, register):
            register_submission(self.submission)

        self.submission.refresh_from_db()
        self.assertEqual(
            self.submission.backend_result,
            {"result": "ok"},
        )

    def test_callback_with_custom_result_serializer(self):
        register = Registry()

        result_uuid = uuid.uuid4()

        # register the callback, including the assertions
        @register(
            "callback",
            "Assertion callback",
            configuration_options=OptionsSerializer,
            backend_feedback_serializer=ResultSerializer,
        )
        def callback(submission, options):
            return {"external_id": result_uuid}

        # call the hook for the submission, while patching the model field registry
        model_field = Form._meta.get_field("registration_backend")
        with patch_registry(model_field, register):
            register_submission(self.submission)

        self.submission.refresh_from_db()
        self.assertEqual(
            self.submission.backend_result,
            {"external_id": str(result_uuid)},
        )
