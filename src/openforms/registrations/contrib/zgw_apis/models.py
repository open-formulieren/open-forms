from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class ZgwConfig(SingletonModel):
    """
    global configuration and defaults
    """

    zrc_service = models.OneToOneField(
        "zgw_consumers.Service",
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.zrc},
        related_name="zgw_zrc_config",
        null=True,
    )
    drc_service = models.OneToOneField(
        "zgw_consumers.Service",
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        related_name="zgw_drc_config",
        null=True,
    )
    ztc_service = models.OneToOneField(
        "zgw_consumers.Service",
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        related_name="zgw_ztc_config",
        null=True,
    )
    # Overridable defaults
    zaaktype = models.URLField(
        max_length=1000, help_text=_("Default URL of the ZAAKTYPE in Catalogi API")
    )
    informatieobjecttype = models.URLField(
        max_length=1000,
        help_text=_("Default URL of the INFORMATIEOBJECTTYPE in Catalogi API"),
    )
    organisatie_rsin = models.CharField(
        max_length=9,
        help_text=_("Default RSIN of organization, which creates the ZAAK"),
    )

    class Meta:
        verbose_name = _("ZGW Configuration")

    def apply_defaults_to(self, options):
        options.setdefault("zaaktype", self.zaaktype)
        options.setdefault("informatieobjecttype", self.informatieobjecttype)
        options.setdefault("organisatie_rsin", self.organisatie_rsin)

    def clean(self):
        # TODO verify zaaktype and informatieobjecttype are part of the configured services
        pass
