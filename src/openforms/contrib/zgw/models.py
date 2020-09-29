from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class ZgwConfig(SingletonModel):
    zrc_service = models.ForeignKey(
        "zgw_consumers.Service",
        null=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"api_type": APITypes.zrc},
        related_name="zrc_config",
    )
    drc_service = models.ForeignKey(
        "zgw_consumers.Service",
        null=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"api_type": APITypes.drc},
        related_name="drc_config",
    )
    zaaktype = models.URLField(
        max_length=1000, help_text=_("URL of the ZAAKTYPE in Catalogi API")
    )
    informatieobjecttype = models.URLField(
        max_length=1000, help_text=_("URL of the INFORMATIEOBJECTTYPE in Catalogi API")
    )
    organisatie_rsin = models.CharField(
        max_length=9, help_text=_("RSIN of organization, which creates the ZAAK")
    )

    class Meta:
        verbose_name = _("ZGW Configuration")
