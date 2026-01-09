import os
import subprocess
import time
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from maykin_common.config import config

from openforms.celery.probes import READINESS_FILE

# real, working Celery broker URL. In CI, the envvar CELERY_BROKER_URL is deliberately
# set to a broken configuration to prevent broken test isolation, but the tests here
# require a real, functionining broker. Most people have redis running locally and CI
# also runs it on localhost, if you need another solution, you can set the
# _CELERY_BROKER_URL environment variable.
CELERY_BROKER_URL: str = config(
    "_CELERY_BROKER_URL", default="redis://localhost:6379/0"
)  # type: ignore
START_WORKER_SCRIPT = Path(settings.BASE_DIR) / "bin" / "celery_worker.sh"


class CeleryTest(TestCase):
    def test_celery_worker_health_check(self):
        """Assert that READINESS_FILE exists after worker has started but not before and not after
        the shutdown
        """
        assert not READINESS_FILE.is_file(), (
            "Celery worker not started but READINESS_FILE found"
        )

        def cleanup():
            if READINESS_FILE.is_file():
                READINESS_FILE.unlink(missing_ok=True)

        self.addCleanup(cleanup)

        # start Celery worker
        process = subprocess.Popen(
            [START_WORKER_SCRIPT],
            cwd=settings.BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={
                **os.environ,
                "CELERY_BROKER_URL": CELERY_BROKER_URL,
                "ENABLE_COVERAGE": os.environ.get("COVERAGE_RUN", ""),
            },
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
