from django.utils.translation import gettext_lazy as _

from django_camunda.camunda_models import ProcessDefinition
from zgw_consumers.drf.serializers import APIModelSerializer

from openforms.plugins.api.serializers import PluginBaseSerializer


class ProcessDefinitionSerializer(APIModelSerializer):
    class Meta:
        model = ProcessDefinition
        fields = ("id", "key", "name", "version")
        extra_kwargs = {
            "key": {
                "help_text": _(
                    "The process definition identifier, used to group different versions."
                ),
            },
            "name": {
                "help_text": _("The human-readable name of the process definition."),
            },
            "version": {
                "help_text": _("The version identifier relative to the 'key'."),
            },
        }


class CamundaPluginSerializer(PluginBaseSerializer):
    pass
