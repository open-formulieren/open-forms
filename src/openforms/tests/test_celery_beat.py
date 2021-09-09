from django.conf import settings
from django.test import SimpleTestCase
from django.utils.module_loading import import_string


class BeatConfigTests(SimpleTestCase):
    def test_task_references_correct(self):
        """
        Assert that the task import paths in the Beat config are valid.
        """
        for entry in settings.CELERY_BEAT_SCHEDULE.values():
            task = entry["task"]
            with self.subTest(task=task):
                try:
                    import_string(task)
                except ImportError:
                    self.fail(
                        f"Could not import task '{task}' in settings.CELERY_BEAT_SCHEDULE"
                    )
