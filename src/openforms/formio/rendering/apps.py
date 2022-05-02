from django.apps import AppConfig


class FormioRenderingConfig(AppConfig):
    name = "openforms.formio.rendering"
    label = "formio_rendering"

    def ready(self):
        # register plugins
        from . import default  # noqa
