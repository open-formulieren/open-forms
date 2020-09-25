from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from ..hal_client import HalClient


class BRPConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("brp_service")


class BRPConfig(SingletonModel):
    brp_service = models.ForeignKey(
        "zgw_consumers.Service",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("BRP service"),
        limit_choices_to={"api_type": APITypes.orc},
        help_text=_("Select which service to use for the BRP API."),
    )

    objects = BRPConfigManager()

    class Meta:
        verbose_name = _("BRP Configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)

    def get_client(self) -> HalClient:
        if not self.brp_service:
            raise RuntimeError("You must configure a BRP service!")

        default_client = self.brp_service.build_client()
        hal_client = HalClient(
            service=default_client.service,
            base_path=default_client.base_path,
        )
        hal_client.auth_value = default_client.auth_header
        return hal_client
