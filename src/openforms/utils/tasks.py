import logging

from django.core import management

from celery_once import QueueOnce

from ..celery import app

logger = logging.getLogger(__name__)


@app.task
def clear_session_store():
    # https://docs.djangoproject.com/en/2.2/topics/http/sessions/#clearing-the-session-store
    logger.debug("Clearing expired sessions")
    management.call_command("clearsessions")


@app.task(base=QueueOnce)
def send_emails() -> None:
    logger.debug("Processing e-mail queue")
    management.call_command("send_mail")
