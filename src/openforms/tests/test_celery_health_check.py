import subprocess
import time
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from openforms.celery import app

READINESS_FILE = Path(settings.BASE_DIR) / "tmp" / "celery_worker_ready"
WORKER = Path(settings.BASE_DIR) / "bin" / "celery_worker.sh"


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
        subprocess.Popen(
            [WORKER],
            cwd=settings.BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # wait for READINESS_FILE to be created, break out as soon as possible
        for i in range(60):
            try:
                assert (
                    READINESS_FILE.is_file()
                ), "Celery worker started but READINESS_FILE not found"
            except AssertionError as ex:
                if i == 59:
                    app.control.shutdown()
                    raise ex
                else:
                    time.sleep(0.1)
            else:
                break

        app.control.shutdown()

        # wait for READINESS_FILE to be deleted, break out as soon as possible
        for i in range(60):
            try:
                assert (
                    not READINESS_FILE.is_file()
                ), "Celery worker terminated but READINESS_FILE not deleted"
            except AssertionError as ex:
                if i == 59:
                    app.control.shutdown()
                    raise ex
                else:
                    time.sleep(0.1)
            else:
                break
