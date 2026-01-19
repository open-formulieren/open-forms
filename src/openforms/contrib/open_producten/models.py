from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class OpenProductenConfig(SingletonModel):
    producten_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Producten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        verbose_name = _("Open Producten configuration")
