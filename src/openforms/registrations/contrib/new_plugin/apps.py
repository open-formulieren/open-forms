from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


# TODO-4908: come up with good name: 'JSON' or '(Form) Variables API'?
class NewPluginConfig(AppConfig):
    name = "openforms.registrations.contrib.new_plugin"
    label = "registrations_new_plugin"
    verbose_name = _("New plugin")

    def ready(self):
        from . import plugin  # noqa
