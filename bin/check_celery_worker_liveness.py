#!/usr/bin/env python
#
# Check the health of a Celery worker.
#
# The worker process writes and periodically touches a number of files that indicate it
# is available and still healthy. If the worker becomes unhealthy for any reason, the
# timestamp of when the heartbeat file was last touched will not update and the delta
# becomes too big, allowing (container) orchestration to terminate and restart the
# worker process.
#
# Example usage with Kubernetes, as a liveness probe:
#
# .. code-block:: yaml
#
#       livenessProbe:
#         exec:
#           command:
#           - python
#           - /app/bin/check_celery_worker_liveness.py
#         initialDelaySeconds: 10
#         periodSeconds: 30  # must be smaller than `MAX_WORKER_LIVENESS_DELTA`
#
# Reference: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/#define-a-liveness-command
#
# Supported environment variables:
#
# * ``MAX_WORKER_LIVENESS_DELTA``: maximum delta between heartbeats before reporting
#   failure, in seconds. Defaults to 60 (one minute).


import os
import sys
import time
from pathlib import Path

HEARTBEAT_FILE = Path(__file__).parent.parent / "tmp" / "celery_worker_heartbeat"
READINESS_FILE = Path(__file__).parent.parent / "tmp" / "celery_worker_ready"
MAX_WORKER_LIVENESS_DELTA = int(os.getenv("MAX_WORKER_LIVENESS_DELTA", 60))  # seconds


# check if worker is ready
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

if time_diff > MAX_WORKER_LIVENESS_DELTA:
    print("Celery worker heartbeat: interval exceeds constraint (60s).")
    sys.exit(1)

print("Celery worker heartbeat found: OK.")
sys.exit(0)
