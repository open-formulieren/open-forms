import logging

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openforms.contrib.objects_api.checks import check_config
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig

from ...base import BasePlugin
from ...registry import register

logger = logging.getLogger(__name__)

PLUGIN_IDENTIFIER = "objects_api"


@register(PLUGIN_IDENTIFIER)
class ObjectsAPIPrefill(BasePlugin):
    verbose_name = _("Objects API")

    def check_config(self):
        check_config()

    def get_config_actions(self):
        return [
            (
                _("Manage API groups"),
                reverse(
                    "admin:registrations_objects_api_objectsapigroupconfig_changelist"
                ),
            ),
            (
                _("Defaults configuration"),
                reverse(
                    "admin:registrations_objects_api_objectsapiconfig_change",
                    args=(ObjectsAPIConfig.singleton_instance_id,),
                ),
            ),
        ]
