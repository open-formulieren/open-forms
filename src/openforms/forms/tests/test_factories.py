from django.test import TestCase

from ..models import FormRegistrationBackend
from .factories import FormFactory, FormStepFactory


class FormFactoryTests(TestCase):
    def test_registration_backend_creates_a_config(self):
        form = FormFactory.create(registration_backend="demo")
        self.assertEqual(form.registration_backends.count(), 1)
        self.assertTrue(FormRegistrationBackend.objects.get(form=form, backend="demo"))

    def test_registration_backend_options_get_passed(self):
        form = FormFactory.create(
            registration_backend="email",
            registration_backend_options={"to_emails": ["me@example.com"]},
        )
        self.assertEqual(form.registration_backends.count(), 1)
        backend = FormRegistrationBackend.objects.get(form=form, backend="email")
        self.assertEqual(backend.options, {"to_emails": ["me@example.com"]})

    def test_registration_backend_options_get_passed_through_subfactories(self):
        form = FormStepFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["me@example.com"]},
        ).form

        self.assertEqual(form.registration_backends.count(), 1)
        backend = FormRegistrationBackend.objects.get(form=form, backend="email")
        self.assertEqual(backend.options, {"to_emails": ["me@example.com"]})
