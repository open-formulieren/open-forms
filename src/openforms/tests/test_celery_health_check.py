import os
import subprocess
import time
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from openforms.celery import READINESS_FILE, app

START_WORKER_SCRIPT = Path(settings.BASE_DIR) / "bin" / "celery_worker.sh"


class CeleryTest(TestCase):
    def setUp(self):
        def shutdown_celery():
            app.control.shutdown()
            if READINESS_FILE.is_file():
                READINESS_FILE.unlink(missing_ok=True)

        self.addCleanup(shutdown_celery)

    def test_celery_worker_health_check(self):
        """Assert that READINESS_FILE exists after worker has started but not before and not after
        the shutdown
        """
        assert (
            not READINESS_FILE.is_file()
        ), "Celery worker not started but READINESS_FILE found"

        # start Celery worker
        process = subprocess.Popen(
            [START_WORKER_SCRIPT],
            cwd=settings.BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "ENABLE_COVERAGE": os.environ.get("COVERAGE_RUN", "")},
        )

        # wait for READINESS_FILE to be created, break out as soon as possible
        start = time.time()
        while (time.time() - start) <= 60:
            if READINESS_FILE.is_file():
                break
            # wait a bit longer...
            time.sleep(1)
        else:
            self.fail("READINESS_FILE was not created within 60 seconds")

        # stop the worker process
        process.terminate()  # sends SIGTERM, (warm) shutting down the worker.
        process.wait(timeout=60)  # wait for process to terminate

        # now assert that the READINESS FILE was deleted as part of the shutdown
        # procedure
        start = time.time()
        while (time.time() - start) <= 60:
            if not READINESS_FILE.is_file():
                break
            # wait a bit longer...
            time.sleep(1)
        else:
            self.fail("READINESS_FILE was not cleaned up within 60 seconds")
