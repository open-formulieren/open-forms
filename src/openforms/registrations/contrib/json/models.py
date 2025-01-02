from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class JSONConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class JSONConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Service"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=True,
        help_text=_("Service for JSON registration plugin"),
    )

    objects = JSONConfigManager()

    class Meta:
        verbose_name = _("JSON registration configuration")
