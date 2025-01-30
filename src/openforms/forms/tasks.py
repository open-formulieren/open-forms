import logging
from datetime import timedelta
from functools import partial

from django.db import DatabaseError, transaction
from django.utils import timezone

from ..celery import app
from .models import Form

logger = logging.getLogger(__name__)


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
