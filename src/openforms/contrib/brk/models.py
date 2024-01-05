from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class BRKConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "service",
            "service__client_certificate",
            "service__server_certificate",
        )


class BRKConfig(SingletonModel):
    """
    Global configuration and defaults.
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("BRK API"),
        help_text=_("Service for API interaction with the BRK."),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    objects = BRKConfigManager()

    class Meta:
        verbose_name = _("BRK configuration")
