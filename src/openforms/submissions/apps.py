from django.apps import AppConfig


class SubmissionsConfig(AppConfig):
    name = "openforms.submissions"
    verbose_name = "Submissions"

    def ready(self):
        # load the signal receivers
        from . import signals  # noqa
