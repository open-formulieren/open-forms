# script for checking readiness + liveness of celery worker

import sys
import time
from pathlib import Path

HEARTBEAT_FILE = Path(__file__).parent.parent / "tmp" / "celery_worker_heartbeat"
READINESS_FILE = Path(__file__).parent.parent / "tmp" / "celery_worker_ready"
TIME_CONSTRAINT = 60  # seconds


# check of worker is ready
if not READINESS_FILE.is_file():
    print("Celery worker not ready.")
    sys.exit(1)

# check if worker is live
if not HEARTBEAT_FILE.is_file():
    print("Celery worker heartbeat not found.")
    sys.exit(1)

# check if worker heartbeat satisfies constraint
stats = HEARTBEAT_FILE.stat()
worker_timestamp = stats.st_mtime
current_timestamp = time.time()
time_diff = current_timestamp - worker_timestamp

if time_diff > TIME_CONSTRAINT:
    print("Celery worker heartbeat: interval exceeds constraint (60s).")
    sys.exit(1)

print("Celery worker heartbeat found: OK.")
sys.exit(0)
