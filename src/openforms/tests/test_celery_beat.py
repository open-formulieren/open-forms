from django.conf import settings
from django.test import SimpleTestCase
from django.utils.module_loading import import_string


class BeatConfigTests(SimpleTestCase):
    def test_task_references_correct(self):
        """
        Assert that the task import paths in the Beat config are valid.
        """
        for entry in settings.CELERY_BEAT_SCHEDULE.values():
            task_path = entry["task"]
            with self.subTest(task=task_path):
                try:
                    task = import_string(task_path)
                except ImportError:
                    self.fail(
                        f"Could not import task '{task_path}' in settings.CELERY_BEAT_SCHEDULE"
                    )
                else:
                    # its is important the full path is used or beat won't be able to find the task
                    if task.name != task_path:
                        self.fail(
                            f"Task '{task_path}' in settings.CELERY_BEAT_SCHEDULE should be registered with it's full import path, eg: '{task.name}'"
                        )
