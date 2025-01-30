import logging
from datetime import timedelta
from functools import partial

from django.db import DatabaseError, transaction
from django.utils import timezone

from celery import chain

from openforms.variables.constants import FormVariableSources

from ..celery import app
from .models import Form

logger = logging.getLogger(__name__)


def on_variables_bulk_update_event(form_id: int) -> None:
    """
    Celery tasks to execute on a "bulk update of variables" event.
    """
    repopulate_reusable_definition_variables_to_form_variables.delay(form_id=form_id)


def on_formstep_save_event(form_id: int, countdown: int) -> None:
    """
    Celery chain of tasks to execute after saving a FormStep.
    """
    create_form_variables_for_components_task = create_form_variables_for_components.si(
        form_id
    )
    repopulate_reusable_definition_variables_task = (
        repopulate_reusable_definition_variables_to_form_variables.si(form_id)
    )

    actions_chain = chain(
        create_form_variables_for_components_task,
        repopulate_reusable_definition_variables_task,
    )
    actions_chain.apply_async(countdown=countdown)


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


@app.task(ignore_result=True)
@transaction.atomic()
def create_form_variables_for_components(form_id: int) -> None:
    """Create FormVariables for each component in the Form

    This task is scheduled after creating/updating a FormStep, to ensure that the saved
    Form has the appropriate FormVariables, even if errors occur in the variables update
    endpoint. This is done to avoid leaving the Form in a broken state.

    See also: https://github.com/open-formulieren/open-forms/issues/4824#issuecomment-2514913073
    """
    from .models import Form, FormVariable  # due to circular import

    form = Form.objects.get(id=form_id)

    # delete the existing form variables, we will re-create them
    FormVariable.objects.filter(
        form=form_id, source=FormVariableSources.component
    ).delete()

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
