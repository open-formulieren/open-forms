from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class ConfigManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        qs = super().get_queryset()
        return qs.select_related(
            "service",
            "service__client_certificate",
            "service__server_certificate",
        )


class JccConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    service = models.OneToOneField(
        "soap.SoapService",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )

    objects = ConfigManager()

    class Meta:
        verbose_name = _("JCC configuration")
