import atexit
from pathlib import Path

from django.conf import settings

import structlog
from celery import bootsteps
from celery.beat import Service as BeatService
from celery.signals import after_task_publish, beat_init, worker_ready, worker_shutdown

logger = structlog.stdlib.get_logger()

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


#
# Utilities for checking the health of celery beat
#

_RUNNING_IN_BEAT = False

BEAT_LIVENESS_FILE = Path(settings.BASE_DIR) / "tmp" / "celery_beat_live"


@beat_init.connect(dispatch_uid="probes.on_beat_init")
def on_beat_init(*, sender: BeatService, **kwargs):
    global _RUNNING_IN_BEAT
    _RUNNING_IN_BEAT = True
    logger.debug("beat_process_marked")
    # on shutdown, clear up the liveness file
    atexit.register(BEAT_LIVENESS_FILE.unlink, missing_ok=True)


@after_task_publish.connect(dispatch_uid="probes.on_beat_task_published")
def on_beat_task_published(*, sender: str, routing_key: str, **kwargs):
    """
    Update the celery beat liveness every time a task is successfully published.

    ``after_task_publish`` fires in the process that sent the task, so we must discern
    between the regular Django app that schedules tasks, and celery beat that also
    schedules tasks. We do this by tapping into the ``beat_init`` signal to mark the
    process as a beat process, and only touch the liveness file when running in beat.
    """
    if not _RUNNING_IN_BEAT:
        return

    logger.debug("beat_task_published", task=sender, routing_key=routing_key)
    # touching the file updates the last modified timestamp, which can be checked by
    # the health-check command
    BEAT_LIVENESS_FILE.touch()
