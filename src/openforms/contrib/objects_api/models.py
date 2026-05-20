from django.db import models
from django.utils.translation import gettext_lazy as _

from zgw_consumers.constants import APITypes

from openforms.utils.validators import validate_rsin


class ObjectsAPIGroupConfig(models.Model):
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("A recognisable name for this set of Objects APIs."),
    )
    identifier = models.SlugField(
        _("identifier"),
        blank=False,
        null=False,
        unique=True,
        help_text=_("A unique, human-friendly identifier to identify this group."),
    )
    objects_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Objects API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=False,
        related_name="+",
    )
    objecttypes_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Objecttypes API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=False,
        related_name="+",
    )
    drc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Documenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        null=True,
        blank=True,
        related_name="+",
    )
    catalogi_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Catalogi API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        null=True,
        blank=True,
        related_name="+",
    )

    #
    # Overridable defaults
    #
    organisatie_rsin = models.CharField(
        _("organisation RSIN"),
        max_length=9,
        blank=True,
        validators=[validate_rsin],
        help_text=_("Default RSIN of organization, which creates the INFORMATIEOBJECT"),
    )

    class Meta:
        verbose_name = _("Objects API group")
        verbose_name_plural = _("Objects API groups")

    def __str__(self) -> str:
        return self.name
