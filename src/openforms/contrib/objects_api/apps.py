from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ObjectsAPIApp(AppConfig):
    name = "openforms.contrib.objects_api"
    label = "objects_api"
    verbose_name = _("Objects API")
