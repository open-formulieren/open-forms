import threading
import time
from unittest.mock import patch

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, tag

from openforms.forms.tasks import (
    recouple_submission_variables_to_form_variables,
    repopulate_reusable_definition_variables_to_form_variables,
)
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormVariableFactory,
)
from openforms.submissions.models import SubmissionValueVariable
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.variables.constants import FormVariableSources


class FormVariableTasksTest(TestCase):
    def test_recouple_submission_variables(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "test1"},
                    {"type": "textfield", "key": "test2"},
                ]
            },
        )
        form_step = form.formstep_set.first()
        submission1 = SubmissionFactory.create(form=form)
        submission2 = SubmissionFactory.create(form=form)

        SubmissionStepFactory.create(
            submission=submission1,
            form_step=form_step,
            data={"test1": "some data 1", "test2": "some data 1"},
        )
        SubmissionStepFactory.create(
            submission=submission2,
            form_step=form_step,
            data={"test1": "some other data 1", "test2": "some other data 1"},
        )

        form.formvariable_set.all().delete()

        self.assertEqual(
            4,
            SubmissionValueVariable.objects.filter(
                submission__form=form, form_variable__isnull=True
            ).count(),
        )

        FormVariableFactory.create(key="test1", form=form)
        FormVariableFactory.create(key="test2", form=form)

        recouple_submission_variables_to_form_variables(form.id)

        self.assertEqual(
            0,
            SubmissionValueVariable.objects.filter(
                submission__form=form, form_variable__isnull=True
            ).count(),
        )

    def test_recouple_reusable_definition_variables(self):
        reusable_fd = FormDefinitionFactory.create(
            is_reusable=True,
            configuration={"components": [{"type": "textfield", "key": "test1"}]},
        )
        form1 = FormFactory.create(
            generate_minimal_setup=True, formstep__form_definition=reusable_fd
        )
        form2 = FormFactory.create(
            generate_minimal_setup=True, formstep__form_definition=reusable_fd
        )

        reusable_fd.configuration = {
            "components": [{"type": "textfield", "key": "test1Updated"}]
        }
        reusable_fd.save()

        repopulate_reusable_definition_variables_to_form_variables(form1.id)

        new_variable = form2.formvariable_set.get()

        self.assertEqual(new_variable.key, "test1Updated")

    def test_recouple_reusable_definition_variables_do_not_delete_user_defined(self):
        reusable_fd = FormDefinitionFactory.create(
            is_reusable=True,
            configuration={"components": [{"type": "textfield", "key": "test1"}]},
        )
        form = FormFactory.create(
            generate_minimal_setup=True, formstep__form_definition=reusable_fd
        )
        user_defined_var = FormVariableFactory.create(
            form=form, key="variable4", user_defined=True
        )

        repopulate_reusable_definition_variables_to_form_variables(form.id)

        form_user_defined_var = form.formvariable_set.get(
            source=FormVariableSources.user_defined
        )

        self.assertEqual(form_user_defined_var, user_defined_var)


class ThreadWithExceptionHandling(threading.Thread):
    def run(self):
        self.exc = None
        try:
            super().run()
        except Exception as e:
            self.exc = e

    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        if self.exc:
            raise self.exc


class FormVariableRaceConditionTasksTest(TransactionTestCase):
    @tag("gh-1970")
    def test_recouple_submission_variables_race_condition(self):
        """
        Race condition:

        The task recouple_submission_variables_to_form_variables starts, it retrieves
        the form variables on a form and tries to relate them to existing submission
        variables.

        While it's processing the submission vars, the form is saved again, triggering
        an update of form variables.

        The task gives an integrity error when saving the submission variables because
        they are being related to non-existing form variables.
        """
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "test1"},
                    {"type": "textfield", "key": "test2"},
                ]
            },
        )
        form_step = form.formstep_set.first()
        submission = SubmissionFactory.create(form=form)

        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"test1": "some data 1", "test2": "some data 1"},
        )

        form.formvariable_set.all().delete()

        FormVariableFactory.create(key="test1", form=form)
        FormVariableFactory.create(key="test2", form=form)

        def recouple_variables_task():
            real_bulk_update = SubmissionValueVariable.objects.bulk_update

            def wrapped_bulk_update(*args, **kwargs):
                time.sleep(0.6)
                # give some time for the delete to complete before we
                # make a DB query
                return real_bulk_update(*args, **kwargs)

            with patch(
                "openforms.submissions.models.submission_value_variable"
                ".SubmissionValueVariableManager.bulk_update",
                wraps=wrapped_bulk_update,
            ) as mock_bulk_update:
                try:
                    recouple_submission_variables_to_form_variables(form.id)
                finally:
                    close_old_connections()
            mock_bulk_update.assert_called_once()

        def race_condition():
            # ensure the delete runs at some point _after_ the
            # recouple_variables_thread has started
            time.sleep(0.5)
            try:
                form.formvariable_set.all().delete()
            finally:
                close_old_connections()

        recouple_variables_thread = ThreadWithExceptionHandling(
            target=recouple_variables_task
        )
        race_condition_thread = threading.Thread(target=race_condition)

        race_condition_thread.start()
        recouple_variables_thread.start()

        race_condition_thread.join()
        recouple_variables_thread.join()
