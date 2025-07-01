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
    zaakbetrokkene_registrator_omschrijving = models.CharField(
        _("description for registrator zaakbetrokkene"),
        max_length=100,
        default="",
        blank=True,
        help_text=_(
            "The 'zaakbetrokkene.omschrijving' value for the employee who registers "
            "the case on behalf of the customer."
        ),
    )
    zaakbetrokkene_partners_omschrijving = models.CharField(
        _("description for zaakbetrokkene partners registration"),
        max_length=100,
        default="",
        blank=True,
        help_text=_(
            "The 'zaakbetrokkene.omschrijving' value for when the partners of the "
            "form submitter are registered as 'betrokkene'."
        ),
    )
    zaakbetrokkene_cosigner_omschrijving = models.CharField(
        _("description for registrator zaakbetrokkene"),
        max_length=100,
        default="mede_initiator",
        blank=True,
        help_text=_(
            "The 'zaakbetrokkene.omschrijving' value for the person who cosigned "
            "the form submission."
        ),
    )

    objects = StufZDSConfigManager()

    class Meta:
        verbose_name = _("StUF-ZDS configuration")
