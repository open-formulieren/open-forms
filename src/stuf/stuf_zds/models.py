from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class StufZDSConfigManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        qs = super().get_queryset()
        return qs.select_related("service", "service__soap_service")


class StufZDSConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "stuf.StufService",
        on_delete=models.PROTECT,
        related_name="stuf_zds_config",
        null=True,
    )
    zaakbetrokkene_partners_omschrijving = models.CharField(
        _("description for zaakbetrokkene partners registration"),
        max_length=100,
        default="",
        blank=True,
        help_text=_(
            "The description that will be added if the zaakbetrokkene registration is "
            "used for the partners."
        ),
    )

    objects = StufZDSConfigManager()

    class Meta:
        verbose_name = _("StUF-ZDS configuration")
