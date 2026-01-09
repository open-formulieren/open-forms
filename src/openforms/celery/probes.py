from pathlib import Path

from django.conf import settings

from celery import bootsteps
from celery.signals import worker_ready, worker_shutdown

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

    def start(self, parent):
        self.tref = parent.timer.call_repeatedly(
            10.0,
            self.update_heartbeat_file,
            (parent,),
            priority=10,
        )

    def stop(self, parent):
        HEARTBEAT_FILE.unlink(missing_ok=True)

    def update_heartbeat_file(self, worker):
        HEARTBEAT_FILE.touch()


@worker_ready.connect
def on_worker_ready(**_):
    READINESS_FILE.touch()


@worker_shutdown.connect
def on_worker_shutdown(**_):
    READINESS_FILE.unlink(missing_ok=True)
