from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FamilyMembersApp(AppConfig):
    name = "openforms.prefill.contrib.family_members"
    label = "prefill_family_members"
    verbose_name = _("Family members prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
