from django.test import TestCase

import reversion
from reversion.models import Revision, Version

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)


class VersionTestCase(TestCase):
    def test_reversion_setup_basics(self):
        """
        run basic versioning operations to test reversion is setup correctly,
         and proof assumptions about how reversion works

        Form and FormStep are always part of same Revision
        FormDefinition is separate
        """

        form = FormFactory(active=True)
        definition = FormDefinitionFactory()
        other_definition = FormDefinitionFactory()
        step = FormStepFactory(form=form, optional=True, form_definition=definition)

        self.assertEqual(Revision.objects.count(), 0)

        with reversion.create_revision():
            # initial revisions
            form.save()
            definition.save()
            step.save()

        with reversion.create_revision():
            form.active = False
            form.save()

        self.assertEqual(Revision.objects.count(), 2)

        # proof objects got versioned
        revision = Revision.objects.last()  # (reversion uses reverse order)
        self.assertTrue(revision.version_set.get_for_object(step).exists())
        self.assertTrue(revision.version_set.get_for_object(definition).exists())
        version = revision.version_set.get_for_object(form).get()
        # proof value got restored to initial value
        version.revert()
        form.refresh_from_db()
        self.assertEqual(form.active, True)

        # change followed object outside revision so we can test reverted data
        step.optional = False
        step.form_definition = other_definition
        step.save()

        # proof latest version of form was restored
        revision = Revision.objects.first()  # (reversion uses reverse order)
        version = revision.version_set.get_for_object(form).get()
        version.revert()
        form.refresh_from_db()
        self.assertEqual(form.active, False)

        # proof step was not reverted by form's revert()
        step.refresh_from_db()
        self.assertEqual(step.optional, False)  # still False from save outside revision

        # proof step gets restored if we revert the whole revision
        revision.revert()
        step.refresh_from_db()
        self.assertEqual(step.optional, True)  # restored to value at latest revision

        # proof the reference to not-followed definition was restored but the object was not part of revision
        self.assertEqual(step.form_definition, definition)
        with self.assertRaises(Version.DoesNotExist):
            revision.version_set.get_for_object(definition).get()
        with self.assertRaises(Version.DoesNotExist):
            revision.version_set.get_for_object(other_definition).get()
