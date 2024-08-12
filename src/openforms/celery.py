from pathlib import Path

from django.conf import settings

from celery import Celery, bootsteps
from celery.signals import worker_ready, worker_shutdown

from .setup import setup_env

setup_env()

app = Celery("open-forms")
app.config_from_object("django.conf:settings", namespace="CELERY")
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
