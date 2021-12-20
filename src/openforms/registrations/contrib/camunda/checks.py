from django.utils.translation import gettext_lazy as _

from django_camunda.client import get_client
from django_camunda.models import CamundaConfig

from openforms.plugins.exceptions import InvalidPluginConfiguration


def check_config():
    # TODO: check that config is valid (CamundaConfig.clean)
    # TODO: check that client can read process definitions
    # maybe: introspect permissions -> check that client can start instances
    pass
