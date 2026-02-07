from datetime import timedelta
from functools import partial

from django.db import DatabaseError, transaction
from django.utils import timezone

import structlog

from openforms.logging import audit_logger

from ..celery import app
from .models import Form

logger = structlog.stdlib.get_logger(__name__)


@app.task(ignore_result=True)
def activate_forms():
    """Activate all the forms that should be activated by the specific date and time."""
    now = timezone.now()
    forms = Form.objects.filter(
        active=False,
        _is_deleted=False,
        activate_on__lte=now,
        activate_on__gt=now - timedelta(minutes=5),
    )

    for form in forms:
        log = logger.bind(form_id=form.pk, name=form.admin_name)
        audit_log = audit_logger.bind(**structlog.get_context(log))
        with transaction.atomic():
            log.info("form_activation")
            try:
                form.activate()
            except DatabaseError as exc:
                log.error("form_activation_failure", exc_info=exc)
            else:
                transaction.on_commit(partial(audit_log.info, "form_activated"))


@app.task(ignore_result=True)
def deactivate_forms():
    """Deactivate all the forms that should be deactivated by the specific date and time."""
    now = timezone.now()
    forms = Form.objects.live().filter(
        deactivate_on__lte=now, deactivate_on__gt=now - timedelta(minutes=5)
    )

    for form in forms:
        log = logger.bind(form_id=form.pk, name=form.admin_name)
        audit_log = audit_logger.bind(**structlog.get_context(log))
        with transaction.atomic():
            log.info("form_deactivation")
            try:
                form.deactivate()
            except DatabaseError as exc:
                log.error("form_deactivation_failure", exc_info=exc)
            else:
                transaction.on_commit(partial(audit_log.info, "form_deactivated"))
