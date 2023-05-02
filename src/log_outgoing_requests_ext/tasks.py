import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from celery import shared_task
from log_outgoing_requests.models import OutgoingRequestsLog

logger = logging.getLogger(__name__)


@shared_task
def cleanup_request_logs() -> int:
    delta = timedelta(hours=settings.LOG_OUTGOING_REQUESTS_MAX_AGE)
    past_timestamp = timezone.now() - delta
    num_deleted, _ = OutgoingRequestsLog.objects.filter(
        timestamp__lte=past_timestamp
    ).delete()
    logger.info("Deleted %d outgoing request log(s)", num_deleted)
    return num_deleted
