from decimal import Decimal

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from django_camunda.utils import TYPE_MAP as CAMUNDA_TYPE_MAP


class CamundaApp(AppConfig):
    name = "openforms.registrations.contrib.camunda"
    label = "registrations_camunda"
    verbose_name = _("Camunda registration plugin")

    def ready(self):
        patch_django_camunda()

        # register plugin
        from . import plugin  # noqa


def patch_django_camunda():
    CAMUNDA_TYPE_MAP[Decimal] = ("Double", lambda val: str(val))
