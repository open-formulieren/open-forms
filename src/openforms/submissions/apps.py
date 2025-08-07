from django.apps import AppConfig

from tablib.formats import registry


class SubmissionsConfig(AppConfig):
    name = "openforms.submissions"
    verbose_name = "Submissions"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from openforms.submissions.exports import ExportFileTypes, XMLKeyValueExport

        # load the signal receivers
        from . import signals  # noqa

        # register custom tablib format
        registry.register(ExportFileTypes.XML.extension, XMLKeyValueExport())
