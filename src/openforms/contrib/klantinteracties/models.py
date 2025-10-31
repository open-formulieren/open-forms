from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class KlantinteractiesManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class KlantinteractiesConfig(SingletonModel):
    """
    Global configuration
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Klantinteracties API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.kc},
        related_name="+",
        null=True,
        help_text=_("The Klantinteracties API service."),
    )

    objects = KlantinteractiesManager()

    class Meta:
        verbose_name = _("Klantinteracties configuration")
