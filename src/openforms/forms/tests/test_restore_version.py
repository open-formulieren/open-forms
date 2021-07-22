import datetime

from django.test import TestCase

from openforms.forms.models import FormDefinition, FormStep, FormVersion
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

EXPORT_BLOB = {
    "forms": '[{"uuid": "324cadce-a627-4e3f-b117-37ca232f16b2", "name": "Test Form 1", "login_required": false, "authentication_backends": ["digid-mock", "digid"], "product": null, "slug": "auth-plugins", "url": "http://testserver/api/v1/forms/324cadce-a627-4e3f-b117-37ca232f16b2", "show_progress_indicator": true, "maintenance_mode": false, "active": true, "is_deleted": false}]',
    "formSteps": '[{"index": 0, "slug": "test-step-1", "form_definition": "http://testserver/api/v1/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8", "form": "http://testserver/api/v1/forms/324cadce-a627-4e3f-b117-37ca232f16b2/steps/3fc61825-1d2d-4db7-a93b-85b21426dc64"}]',
    "formDefinitions": '[{"url": "http://testserver/api/v1/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8", "uuid": "f0dad93b-333b-49af-868b-a6bcb94fa1b8", "name": "Test Definition 1", "slug": "test-definition-1", "configuration": {"test": "1"}}]',
}


class RestoreVersionTest(TestCase):
    def test_restoring_version(self):
        form_definition = FormDefinitionFactory.create(
            name="Test Definition 2", configuration={"test": "2"}
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            date_creation=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        self.assertEqual(1, FormVersion.objects.all().count())
        self.assertEqual(1, FormDefinition.objects.all().count())

        form.restore_old_version(version)
        form.refresh_from_db()

        self.assertEqual(1, FormVersion.objects.all().count())
        self.assertEqual("Test Form 1", form.name)
        self.assertEqual(2, FormDefinition.objects.all().count())

        form_steps = FormStep.objects.filter(form=form)

        self.assertEqual(1, form_steps.count())

        restored_form_definition = form_steps.get().form_definition

        self.assertEqual("Test Definition 1", restored_form_definition.name)
        self.assertEqual("test-definition-1", restored_form_definition.slug)
        self.assertEqual({"test": "1"}, restored_form_definition.configuration)

    def test_form_definition_same_slug_different_configuration(self):
        """Test that restoring a form definition with a slug that matches the slug of another form definition
        (but has a different configuration) creates a new form definition with a modified slug.
        """
        form_definition = FormDefinitionFactory.create(
            slug="test-definition-1", configuration={"test": "2"}
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            date_creation=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        form.restore_old_version(version)
        form.refresh_from_db()

        self.assertEqual(1, FormVersion.objects.all().count())
        self.assertEqual(2, FormDefinition.objects.all().count())

        form_steps = FormStep.objects.filter(form=form)

        self.assertEqual(1, form_steps.count())

        restored_form_definition = form_steps.get().form_definition

        self.assertEqual("test-definition-1-2", restored_form_definition.slug)

    def test_restore_twice_a_version(self):
        form_definition = FormDefinitionFactory.create(
            slug="test-definition-2", configuration={"test": "2"}
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            date_creation=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        for _ in range(2):
            form.restore_old_version(version)
            form.refresh_from_db()

        self.assertEqual(2, FormDefinition.objects.all().count())

    def test_form_definition_same_slug_same_configuration(self):
        """Test that restoring a form definition with a slug that matches the slug of another form definition
        (and has the same configuration) links to the existing form definition.
        """
        form_definition = FormDefinitionFactory.create(
            slug="test-definition-1", configuration={"test": "1"}
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)

        version = FormVersion.objects.create(
            form=form,
            date_creation=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        form.restore_old_version(version)
        form.refresh_from_db()

        self.assertEqual(1, FormVersion.objects.all().count())
        self.assertEqual(1, FormDefinition.objects.all().count())

        form_steps = FormStep.objects.filter(form=form)

        self.assertEqual(1, form_steps.count())

        restored_form_definition = form_steps.get().form_definition

        self.assertEqual(form_definition, restored_form_definition)
