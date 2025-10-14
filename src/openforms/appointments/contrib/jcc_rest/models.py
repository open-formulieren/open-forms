from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class JccRestConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class JccRestConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("JCC Rest API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    objects = JccRestConfigManager()

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        verbose_name = _("JCC Rest configuration")
