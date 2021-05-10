from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from openforms.utils.validators import validate_rsin


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
        max_length=1000,
        blank=True,
        help_text=_("Default URL of the ZAAKTYPE in Catalogi API"),
    )
    informatieobjecttype = models.URLField(
        max_length=1000,
        blank=True,
        help_text=_("Default URL of the INFORMATIEOBJECTTYPE in Catalogi API"),
    )
    organisatie_rsin = models.CharField(
        max_length=9,
        blank=True,
        validators=[validate_rsin],
        help_text=_("Default RSIN of organization, which creates the ZAAK"),
    )

    class Meta:
        verbose_name = _("ZGW Configuration")

    def apply_defaults_to(self, options):
        options.setdefault("zaaktype", self.zaaktype)
        options.setdefault("informatieobjecttype", self.informatieobjecttype)
        options.setdefault("organisatie_rsin", self.organisatie_rsin)

    def clean(self):
        super().clean()

        if self.zrc_service and self.zaaktype:
            if not self.zaaktype.startswith(self.zrc_service.api_root):
                raise ValidationError(
                    {"zaaktype": _("Zaaktype is not part of ZRC service's API root")}
                )

        if self.ztc_service and self.informatieobjecttype:
            if not self.informatieobjecttype.startswith(self.ztc_service.api_root):
                raise ValidationError(
                    {
                        "informatieobjecttype": _(
                            "Informatieobjecttype is not part of ZTC service's API root"
                        )
                    }
                )
