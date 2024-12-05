from unittest.mock import patch

from django.urls import reverse
from django.utils.translation import gettext as _

from rest_framework import serializers, status
from rest_framework.test import APITestCase

from openforms.accounts.models import User
from openforms.accounts.tests.factories import SuperUserFactory
from openforms.payments.base import BasePlugin as PaymentBasePlugin
from openforms.payments.registry import Registry as PaymentRegistry
from openforms.registrations.base import BasePlugin as RegistrationBasePlugin
from openforms.registrations.registry import Registry as RegistrationRegistry
from openforms.registrations.tests.utils import patch_registry

from ..models import Form, FormRegistrationBackend
from .factories import FormFactory, FormRegistrationBackendFactory


class EmailOptionsSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class RegistrationPlugin(RegistrationBasePlugin):
    configuration_options = EmailOptionsSerializer

    def register_submission(self, submission, options):
        pass


class PaymentPlugin(PaymentBasePlugin):
    configuration_options = EmailOptionsSerializer


class FormPluginOptionTest(APITestCase):
    user: User

    def setUp(self):
        super().setUp()
        self.user = SuperUserFactory.create()
        self.client.force_authenticate(user=self.user)

    def test_registration_backend_options(self):
        form = FormFactory.create()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        model_field = FormRegistrationBackend._meta.get_field("backend")

        register = RegistrationRegistry()
        register("test")(RegistrationPlugin)

        patcher = patch(
            "openforms.forms.api.serializers.form.registration_register", new=register
        )
        with patcher, patch_registry(model_field, register):
            with self.subTest("blank"):
                response = self.client.patch(
                    url,
                    data={
                        "registration_backends": [],
                    },
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                form.refresh_from_db()
                self.assertEqual(form.registration_backends.count(), 0)

            with self.subTest("valid"):
                response = self.client.patch(
                    url,
                    data={
                        "registration_backends": [
                            {
                                "backend": "test",
                                "options": {"email": "foo@bar.baz"},
                            }
                        ]
                    },
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                form.refresh_from_db()
                backend = form.registration_backends.first()
                self.assertEqual(backend.backend, "test")
                self.assertEqual(backend.options, {"email": "foo@bar.baz"})

            with self.subTest("invalid"):
                response = self.client.patch(
                    url,
                    data={
                        "registration_backends": [
                            {
                                "backend": "test",
                                "options": {"email": "not_email_address"},
                            }
                        ]
                    },
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

                json = response.json()
                self.assertEqual(json["code"], "invalid")
                self.assertEqual(
                    json["invalidParams"][0]["name"],
                    "registrationBackends.0.options.email",
                )

    def test_payment_backend_options(self):
        form = FormFactory.create()

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        model_field = Form._meta.get_field("payment_backend")

        register = PaymentRegistry()
        register("test")(PaymentPlugin)

        patcher = patch(
            "openforms.forms.api.serializers.form.payment_register", new=register
        )
        with patcher, patch_registry(model_field, register):
            with self.subTest("blank"):
                response = self.client.patch(
                    url,
                    data={
                        "payment_backend": "",
                        "payment_backend_options": None,
                    },
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                form.refresh_from_db()
                self.assertEqual(form.payment_backend, "")
                self.assertEqual(form.payment_backend_options, None)

            with self.subTest("valid"):
                response = self.client.patch(
                    url,
                    data={
                        "payment_backend": "test",
                        "payment_backend_options": {"email": "foo@bar.baz"},
                    },
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                form.refresh_from_db()
                self.assertEqual(form.payment_backend, "test")
                self.assertEqual(form.payment_backend_options, {"email": "foo@bar.baz"})

            with self.subTest("invalid"):
                response = self.client.patch(
                    url,
                    data={
                        "payment_backend": "test",
                        "payment_backend_options": {"email": "not_email_address"},
                    },
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

                json = response.json()
                self.assertEqual(json["code"], "invalid")
                self.assertEqual(
                    json["invalidParams"][0]["name"], "paymentBackendOptions.email"
                )

    def test_overwrite_only_registration_email_subject_templates(self):
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="fst",
            backend="email",
            options={"to_emails": ["test@test.nl"]},
        )

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.patch(
            url,
            data={
                "registration_backends": [
                    {
                        "key": "fst",
                        "backend": "email",
                        "options": {
                            "to_emails": ["test@test.nl"],
                            "email_subject": "Custom subject",
                        },
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["registrationBackends"]), 1)
        backend = data["registrationBackends"][0]
        self.assertEqual(
            backend["options"]["emailSubject"],
            "Custom subject",
        )
        self.assertEqual(backend["key"], "fst")

    def test_overwrite_both_registration_email_html_and_text_templates(self):
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="fst",
            backend="email",
            options={"to_emails": ["test@test.nl"]},
        )

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.patch(
            url,
            data={
                "registration_backends": [
                    {
                        "backend": "email",
                        "options": {
                            "to_emails": ["test@test.nl"],
                            "email_content_template_html": "Custom HTML template",
                            "email_content_template_text": "Custom text template",
                        },
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["registrationBackends"]), 1)
        backend = data["registrationBackends"][0]

        self.assertNotIn("emailSubject", backend["options"])
        self.assertNotIn("paymentSubject", backend["options"])
        self.assertEqual(
            backend["options"]["emailContentTemplateHtml"],
            "Custom HTML template",
        )
        self.assertEqual(
            backend["options"]["emailContentTemplateText"],
            "Custom text template",
        )

    def test_cannot_overwrite_only_registration_email_html_template(self):
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="fst",
            backend="email",
            options={"to_emails": ["test@test.nl"]},
        )

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.patch(
            url,
            data={
                "registration_backends": [
                    {
                        "backend": "email",
                        "options": {
                            "to_emails": ["test@test.nl"],
                            "email_content_template_html": "Custom HTML template",
                        },
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()
        error = data["invalidParams"][0]["reason"]

        self.assertEqual(
            error,
            _(
                "The fields {fields} must all have a non-empty value as soon as one of them "
                "does."
            ).format(fields="email_content_template_html, email_content_template_text"),
        )
