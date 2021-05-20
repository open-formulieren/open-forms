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
        verbose_name=_("Zaken API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.zrc},
        related_name="zgw_zrc_config",
        null=True,
    )
    drc_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Documenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        related_name="zgw_drc_config",
        null=True,
    )
    ztc_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Catalogi API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        related_name="zgw_ztc_config",
        null=True,
    )
    # Overridable defaults
    zaaktype = models.URLField(
        _("zaaktype"),
        max_length=1000,
        blank=True,
        help_text=_("Default URL of the ZAAKTYPE in the Catalogi API"),
    )
    informatieobjecttype = models.URLField(
        _("informatieobjecttype"),
        max_length=1000,
        blank=True,
        help_text=_("Default URL of the INFORMATIEOBJECTTYPE in the Catalogi API"),
    )
    organisatie_rsin = models.CharField(
        _("organisatie RSIN"),
        max_length=9,
        blank=True,
        validators=[validate_rsin],
        help_text=_("Default RSIN of organization, which creates the ZAAK"),
    )

    class Meta:
        verbose_name = _("ZGW API's configuration")

    def apply_defaults_to(self, options):
        options.setdefault("zaaktype", self.zaaktype)
        options.setdefault("informatieobjecttype", self.informatieobjecttype)
        options.setdefault("organisatie_rsin", self.organisatie_rsin)

    def clean(self):
        super().clean()

        if self.ztc_service and self.zaaktype:
            if not self.zaaktype.startswith(self.ztc_service.api_root):
                raise ValidationError(
                    {"zaaktype": _("ZAAKTYPE is not part of the Catalogi API")}
                )

        if self.ztc_service and self.informatieobjecttype:
            if not self.informatieobjecttype.startswith(self.ztc_service.api_root):
                raise ValidationError(
                    {
                        "informatieobjecttype": _(
                            "INFORMATIEOBJECTTYPE is not part of the Catalogi API"
                        )
                    }
                )
