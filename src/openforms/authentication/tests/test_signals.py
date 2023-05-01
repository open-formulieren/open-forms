from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import tag

from rest_framework.test import APIRequestFactory, APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import FORM_AUTH_SESSION_KEY
from ..registry import Registry
from ..signals import set_auth_attribute_on_session
from .mocks import RequiresAdminPlugin, mock_register

factory = APIRequestFactory()


class SetSubmissionIdentifyingAttributesTests(APITestCase):
    def test_attributes_not_set_for_demo_plugin_without_staff(self):
        register = Registry()
        register("plugin1")(RequiresAdminPlugin)
        instance = SubmissionFactory.create()
        request = factory.get("/foo")
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "plugin": "plugin1",
                "attribute": RequiresAdminPlugin.provides_auth,
                "value": "123",
            }
        }

        invalid_users = (
            AnonymousUser(),
            UserFactory.build(),
        )

        for user in invalid_users:
            with self.subTest(user_type=str(type(user)), is_staff=user.is_staff):
                request.user = user

                with mock_register(register):
                    with self.assertRaises(PermissionDenied):
                        set_auth_attribute_on_session(
                            sender=None, instance=instance, request=request
                        )

                instance.refresh_from_db()
                self.assertFalse(hasattr(instance, "auth_info"))

    def test_attribute_set_for_demo_plugin_with_staff_user(self):
        register = Registry()
        register("plugin1")(RequiresAdminPlugin)
        instance = SubmissionFactory.create()
        request = factory.get("/foo")
        request.user = StaffUserFactory.build()
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "plugin": "plugin1",
                "attribute": RequiresAdminPlugin.provides_auth,
                "value": "123",
            }
        }

        with mock_register(register):
            set_auth_attribute_on_session(
                sender=None, instance=instance, request=request
            )

        instance.refresh_from_db()
        self.assertEqual(instance.auth_info.value, "123")

    @tag("gh-1959")
    def test_setting_auth_attributes_flips_hashed_flag(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form_url="http://tests/myform/",
            auth_info__plugin="digid",
            auth_info__value="123456789",
            auth_info__attribute="bsn",
        )

        submission.auth_info.hash_identifying_attributes()

        self.assertTrue(submission.auth_info.attribute_hashed)

        user = StaffUserFactory()

        request = factory.get("/foo")
        request.user = user
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "plugin": "digid",
                "attribute": "bsn",
                "value": "123456789",
            }
        }

        set_auth_attribute_on_session(sender=None, instance=submission, request=request)

        submission.refresh_from_db()

        self.assertEqual(submission.auth_info.value, "123456789")
        self.assertFalse(submission.auth_info.attribute_hashed)
