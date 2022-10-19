from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import override_settings
from django.test.client import RequestFactory

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import (
    FORM_AUTH_SESSION_KEY,
    REGISTRATOR_SUBJECT_SESSION_KEY,
    AuthAttribute,
)
from ..registry import Registry
from ..signals import set_auth_attribute_on_session
from .mocks import Plugin, RequiresAdminPlugin, mock_register
from ..views import AuthenticationReturnView

factory = APIRequestFactory()


class ProvidesEmployeePlugin(Plugin):
    provides_auth = AuthAttribute.employee_id


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

    def test_attributes_set_with_registrator_subject_info(self):
        register = Registry()
        register("organization_plugin")(ProvidesEmployeePlugin)
        instance = SubmissionFactory.create()
        request = factory.get("/foo")
        request.user = StaffUserFactory.build()
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "plugin": "organization_plugin",
                "attribute": AuthAttribute.employee_id,
                "value": "my-employee-id",
            },
            REGISTRATOR_SUBJECT_SESSION_KEY: {
                "attribute": AuthAttribute.bsn,
                "value": "123",
            },
        }

        with mock_register(register):
            set_auth_attribute_on_session(
                sender=None, instance=instance, request=request
            )

        instance.refresh_from_db()

        # check the property doesn't alias both
        self.assertNotEqual(instance.auth_info, instance.registrator)

        # check the clients info is stored as .registrator
        self.assertEqual(instance.auth_info.attribute, AuthAttribute.bsn)
        self.assertEqual(instance.auth_info.value, "123")
        # TODO check what we want from this
        # self.assertEqual(instance.auth_info.plugin, "registrator")

        # check the employee's info is stored as .registrator
        self.assertEqual(instance.registrator.plugin, "organization_plugin")
        self.assertEqual(instance.registrator.attribute, AuthAttribute.employee_id)
        self.assertEqual(instance.registrator.value, "my-employee-id")

    def test_attributes_set_with_registrator_when_skipped(self):
        register = Registry()
        register("organization_plugin")(ProvidesEmployeePlugin)
        instance = SubmissionFactory.create()
        request = factory.get("/foo")
        request.user = StaffUserFactory.build()
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "plugin": "organization_plugin",
                "attribute": AuthAttribute.employee_id,
                "value": "my-employee-id",
            },
            REGISTRATOR_SUBJECT_SESSION_KEY: {
                "skipped_subject_info": True,
            },
        }

        with mock_register(register):
            set_auth_attribute_on_session(
                sender=None, instance=instance, request=request
            )

        instance.refresh_from_db()

        # check the property aliases both
        self.assertEqual(instance.auth_info, instance.registrator)

        # check the employee's info is stored as .auth_info
        self.assertEqual(instance.auth_info.plugin, "organization_plugin")
        self.assertEqual(instance.auth_info.attribute, AuthAttribute.employee_id)
        self.assertEqual(instance.auth_info.value, "my-employee-id")

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://foo.bar"]
    )
    def test_successful_auth_sends_signal(self):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["plugin1"],
            form_definition__login_required=True,
        )
        form = step.form

        # we need an arbitrary request
        factory = APIRequestFactory()
        init_request = factory.get("/foo")
        url = plugin.get_return_url(init_request, form)
        next_url = "http://foo.bar"
        request = factory.get(url, {"next": next_url})

        # Add session information to the request:
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "plugin": "plugin1",
                "attribute": Plugin.provides_auth,
                "value": "123",
            }
        }

        return_view = AuthenticationReturnView.as_view(register=register)

        with patch(
            "openforms.authentication.views.authentication_success.send"
        ) as m_send:
            response = return_view(request, slug=form.slug, plugin_id=plugin.identifier)

            self.assertEqual(response.status_code, 302)
            m_send.assert_called_once()
            call_args = m_send.call_args.kwargs
            self.assertIn("sender", call_args)
            self.assertIn("request", call_args)
            self.assertEqual(AuthenticationReturnView, call_args["sender"])
            self.assertTrue(isinstance(call_args["request"], Request))

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://foo.bar"]
    )
    def test_unsuccessful_auth_does_not_sends_signal(self):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["plugin1"],
            form_definition__login_required=True,
        )
        form = step.form

        # we need an arbitrary request
        factory = RequestFactory()
        init_request = factory.get("/foo")
        url = plugin.get_return_url(init_request, form)
        next_url = "http://foo.bar"
        request = factory.get(url, {"next": next_url})

        return_view = AuthenticationReturnView.as_view(register=register)

        # No FORM_AUTH_SESSION_KEY in the session, since auth was unsuccessful
        request.session = {}

        with patch(
            "openforms.authentication.views.authentication_success.send"
        ) as m_send:
            response = return_view(request, slug=form.slug, plugin_id=plugin.identifier)

            self.assertEqual(response.status_code, 302)
            m_send.assert_not_called()
