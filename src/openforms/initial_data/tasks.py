from functools import partial

from django.db import transaction
from django.db.models import F
from django.utils import timezone

import structlog

from openforms.celery import app

from .models import InitialSubmissionData

logger = structlog.stdlib.get_logger(__name__)


@app.task(ignore_result=True)
@transaction.atomic()
def cleanup_expired_initial_data() -> None:
    """
    Delete tasks with an expiry date in the past.
    """
    expired = InitialSubmissionData.objects.annotate(
        _expiry_date=F("created_on") + F("ttl")
    ).filter(_expiry_date__lt=timezone.now())
    num_deleted, _ = expired.delete()
    transaction.on_commit(
        partial(
            logger.info,
            "expired_initial_data_cleanup_completed",
            num_deleted=num_deleted,
        ),
    )
