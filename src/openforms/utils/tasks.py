import logging
from ..celery import app
from django.core import management

logger = logging.getLogger(__name__)


@app.task
def clear_session_store():
    # Reference https://docs.djangoproject.com/en/3.2/topics/http/sessions/#clearing-the-session-store
    logger.info('I am a running celery beat task')
#    management.call_command("clearsessions", verbosity=0)

