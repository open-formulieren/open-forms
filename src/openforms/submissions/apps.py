from django.apps import AppConfig

from tablib.formats import registry


class SubmissionsConfig(AppConfig):
    name = "openforms.submissions"
    verbose_name = "Submissions"

    def ready(self):
        from openforms.submissions.exports import ExportFileTypes, XMLKeyValueExport

        # load the signal receivers
        from . import signals  # noqa

        # register custom tablib format
        registry.register(ExportFileTypes.XML.extension, XMLKeyValueExport())
