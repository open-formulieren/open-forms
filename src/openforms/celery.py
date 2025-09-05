import logging  # noqa: TID251 - correct use to replace stdlib logging
import logging.config  # noqa: TID251 - correct use to replace stdlib logging
from pathlib import Path

from django.conf import settings

import structlog
from celery import Celery, bootsteps
from celery.signals import setup_logging, worker_ready, worker_shutdown
from django_structlog.celery.steps import DjangoStructLogInitStep

from openforms.conf.utils import config

from .setup import setup_env

setup_env()

app = Celery("open-forms")
assert app.steps is not None
app.steps["worker"].add(DjangoStructLogInitStep)
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.broker_transport_options = {
    # only used when the broker uses redis sentinel. Failing to specify a master name
    # when the broker is configured with sentinel will trigger a `ValueError` in workers.
    "master_name": config("REDIS_BROKER_SENTINEL_MASTER", default="") or None,
    # Optional authentication parameters
    "sentinel_kwargs": {
        "password": config("REDIS_BROKER_SENTINEL_PASSWORD", default="") or None,
        "username": config("REDIS_BROKER_SENTINEL_USERNAME", default="") or None,
    },
}
app.conf.result_backend_transport_options = {
    # only used when the broker uses redis sentinel. Failing to specify a master name
    # when the broker is configured with sentinel will trigger a `ValueError` in workers.
    "master_name": config("REDIS_RESULT_BACKEND_SENTINEL_MASTER", default="") or None,
    # Optional authentication parameters
    "sentinel_kwargs": {
        "password": config("REDIS_RESULT_BACKEND_SENTINEL_PASSWORD", default="")
        or None,
        "username": config("REDIS_RESULT_BACKEND_SENTINEL_USERNAME", default="")
        or None,
    },
}
app.conf.ONCE = {
    "backend": "celery_once.backends.Redis",
    "settings": {
        "url": settings.CELERY_ONCE_REDIS_URL,
        "default_timeout": 60 * 60,  # one hour
    },
}


app.autodiscover_tasks()

HEARTBEAT_FILE = Path(settings.BASE_DIR) / "tmp" / "celery_worker_heartbeat"
READINESS_FILE = Path(settings.BASE_DIR) / "tmp" / "celery_worker_ready"


@setup_logging.connect
def receiver_setup_logging(
    loglevel, logfile, format, colorize, **kwargs
):  # pragma: no cover
    formatter = config("LOG_FORMAT_CONSOLE", default="json")
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                    "foreign_pre_chain": [
                        structlog.contextvars.merge_contextvars,
                        structlog.processors.TimeStamper(fmt="iso"),
                        structlog.stdlib.add_logger_name,
                        structlog.stdlib.add_log_level,
                        structlog.stdlib.PositionalArgumentsFormatter(),
                    ],
                },
                "plain_console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(),
                    "foreign_pre_chain": [
                        structlog.contextvars.merge_contextvars,
                        structlog.processors.TimeStamper(fmt="iso"),
                        structlog.stdlib.add_logger_name,
                        structlog.stdlib.add_log_level,
                        structlog.stdlib.PositionalArgumentsFormatter(),
                    ],
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": formatter,
                },
            },
            "loggers": {
                "openforms": {
                    "handlers": ["console"],
                    "level": "INFO",
                },
                "django_structlog": {
                    "handlers": ["console"],
                    "level": "INFO",
                },
            },
        }
    )

    exception_processors = (
        [structlog.processors.format_exc_info] if formatter == "json" else []
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            *exception_processors,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


#
# Utilities for checking the health of celery workers
#
class LivenessProbe(bootsteps.StartStopStep):
    requires = {"celery.worker.components:Timer"}

    def __init__(self, worker, **kwargs):
        self.requests = []
        self.tref = None

    def start(self, worker):
        self.tref = worker.timer.call_repeatedly(
            10.0,
            self.update_heartbeat_file,
            (worker,),
            priority=10,
        )

    def stop(self, worker):
        HEARTBEAT_FILE.unlink(missing_ok=True)

    def update_heartbeat_file(self, worker):
        HEARTBEAT_FILE.touch()


@worker_ready.connect
def worker_ready(**_):
    READINESS_FILE.touch()


@worker_shutdown.connect
def worker_shutdown(**_):
    READINESS_FILE.unlink(missing_ok=True)


app.steps["worker"].add(LivenessProbe)
