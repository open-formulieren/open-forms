import copy
import logging
from datetime import timedelta
from functools import partial

from django.db import DatabaseError, transaction
from django.db.utils import IntegrityError
from django.utils import timezone

from celery import chain
from djangorestframework_camel_case.util import camelize

from openforms.variables.constants import FormVariableSources

from ..celery import app
from .models import Form

logger = logging.getLogger(__name__)


def on_variables_bulk_update_event(form_id: int) -> None:
    """
    Celery chain of tasks to execute on a bulk update of variables event.
    """
    repopulate_reusable_definition_variables_task = (
        repopulate_reusable_definition_variables_to_form_variables.si(form_id)
    )
    recouple_submission_variables_task = (
        recouple_submission_variables_to_form_variables.si(form_id)
    )

    actions_chain = chain(
        repopulate_reusable_definition_variables_task,
        recouple_submission_variables_task,
    )
    actions_chain.delay()


@app.task(ignore_result=True)
def detect_formiojs_configuration_snake_case(
    form_definition_id: int, raise_exception=False
):
    """
    Detect if the JSON configuration from formiojs contains snake_case keys.

    JSON and Javascript convention is to use camelCase, and our API endpoints convert
    between camelCase and snake_case. The :attr:`FormDefinition.configuration` attribute
    should only contain camelCase keys as it's a literal object managed by formiojs.

    This task should be invoked on saves of FormDefinition objects to monitor for
    mistakes in API endpoints, see github issue #449 for an example of such a mistake.
    """
    from .models import FormDefinition
    from .utils import remove_key_from_dict

    fd = FormDefinition.objects.filter(id=form_definition_id).first()
    if fd is None:  # in case the record does not exist (anymore) in the DB
        return

    config_now = copy.deepcopy(fd.configuration)
    remove_key_from_dict(config_now, "time_24hr")
    remove_key_from_dict(config_now, "invalid_time")
    camelized_config = camelize(config_now)

    if config_now != camelized_config:
        error_msg = (
            "FormDefinition with ID %d appears to contain snake_case keys in its "
            "Form.io configuration. This is known to cause issues with the prefill "
            "module."
        )
        error_msg_args = (form_definition_id,)
        logger.error(error_msg, *error_msg_args)
        if raise_exception:
            raise Exception(error_msg % error_msg_args)


@app.task(ignore_result=True)
def recouple_submission_variables_to_form_variables(form_id: int) -> None:
    """Recouple SubmissionValueVariable to FormVariable

    When the FormVariable bulk create/update endpoint is called, all existing FormVariable related to the form are
    deleted and new are created. If there are existing submissions for this form, the SubmissionValueVariables don't
    have a related FormVariable anymore. This task tries to recouple them.
    """
    from openforms.submissions.models import SubmissionValueVariable

    form = Form.objects.get(id=form_id)
    submission_variables_to_recouple = SubmissionValueVariable.objects.filter(
        form_variable__isnull=True, submission__form=form
    )

    form_variables = {
        variable.key: variable for variable in form.formvariable_set.all()
    }

    submission_variables_to_update = []
    for submission_variable in submission_variables_to_recouple:
        if form_variable := form_variables.get(submission_variable.key):
            submission_variable.form_variable = form_variable
            submission_variables_to_update.append(submission_variable)

    try:
        SubmissionValueVariable.objects.bulk_update(
            submission_variables_to_update, fields=["form_variable"]
        )
    except IntegrityError:
        # Issue #1970: If the form is saved again from the form editor while this task was running, the form variables
        # retrieved don't exist anymore. Another task will be scheduled from the endpoint, so nothing more to do here.
        logger.info("Form variables were updated while this task was runnning.")


@app.task(ignore_result=True)
@transaction.atomic()
def repopulate_reusable_definition_variables_to_form_variables(form_id: int) -> None:
    """Fix inconsistencies created by updating a re-usable form definition which is used in other forms.

    When the FormVariable bulk create/update endpoint is called, all existing FormVariable related to the form are
    deleted and new are created. If there are any form definitions which are reusable, we want to update all the forms
    which are also using these FormDefinitions (concerning the FormVariables). This task updates the FormVariables
    of each related form in the database, by replacing the old state with the newly derived set of form variables.
    """
    from .models import FormDefinition, FormVariable  # due to circular import

    fds = FormDefinition.objects.filter(formstep__form=form_id, is_reusable=True)

    other_forms = Form.objects.filter(formstep__form_definition__in=fds).exclude(
        id=form_id
    )

    # delete the existing form variables, we will re-create them
    FormVariable.objects.filter(
        form__in=other_forms, source=FormVariableSources.component
    ).delete()

    for form in other_forms:
        FormVariable.objects.create_for_form(form)


@app.task()
def activate_forms():
    """Activate all the forms that should be activated by the specific date and time."""
    from openforms.logging import logevent

    now = timezone.now()
    forms = Form.objects.filter(
        active=False,
        _is_deleted=False,
        activate_on__lte=now,
        activate_on__gt=now - timedelta(minutes=5),
    )

    for form in forms:
        with transaction.atomic():
            try:
                form.activate()
            except DatabaseError as exc:
                logger.error(
                    "Form activation of form %s failed",
                    form.admin_name,
                    exc_info=exc,
                    extra={"pk": form.pk},
                )
            else:
                transaction.on_commit(partial(logevent.form_activated, form))


@app.task()
def deactivate_forms():
    """Deactivate all the forms that should be deactivated by the specific date and time."""
    from openforms.logging import logevent

    now = timezone.now()
    forms = Form.objects.live().filter(
        deactivate_on__lte=now, deactivate_on__gt=now - timedelta(minutes=5)
    )

    for form in forms:
        with transaction.atomic():
            try:
                form.deactivate()
            except DatabaseError as exc:
                logger.error(
                    "Form deactivation of form %s failed",
                    form.admin_name,
                    exc_info=exc,
                    extra={"pk": form.pk},
                )

            else:
                transaction.on_commit(partial(logevent.form_deactivated, form))
