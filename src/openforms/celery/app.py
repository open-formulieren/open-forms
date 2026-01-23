from celery import Celery
from celery.signals import setup_logging
from django_structlog.celery.steps import DjangoStructLogInitStep
from maykin_common.health_checks.celery.probes import EventLoopProbe

from .logging import receiver_setup_logging

app = Celery("open-forms")
app.config_from_object("django.conf:settings", namespace="CELERY")

setup_logging.connect(receiver_setup_logging)

assert app.steps is not None
app.steps["worker"].add(DjangoStructLogInitStep)
app.steps["worker"].add(EventLoopProbe)

app.autodiscover_tasks()
