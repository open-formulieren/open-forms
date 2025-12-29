import os
import sys
import time
from pathlib import Path

from celery.beat import PersistentScheduler

HEARTBEAT_FILE = Path(__file__).parent.parent / "tmp" / "celery_beat_heartbeat"
MAX_BEAT_LIVENESS_DELTA = int(os.getenv("MAX_BEAT_LIVENESS_DELTA", 60))  # seconds


class HealthcheckScheduler(PersistentScheduler):
    """
    Custom Celery Beat scheduler that writes a heartbeat file on every scheduler tick.
    """

    def tick(self):
        HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
        HEARTBEAT_FILE.write_text(str(time.time()))
        return super().tick()


def run_healthcheck():
    """
    Docker healthcheck entry point.
    """
    if not HEARTBEAT_FILE.is_file():
        print("Celery Beat heartbeat file missing", flush=True)
        sys.exit(1)

    age = time.time() - HEARTBEAT_FILE.stat().st_mtime
    if age > MAX_BEAT_LIVENESS_DELTA:
        print(f"Celery Beat heartbeat stale ({age:.1f}s)", flush=True)
        sys.exit(1)

    print("Celery Beat healthy", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    run_healthcheck()
