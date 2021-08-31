from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from openforms.utils.validators import validate_rsin


class ObjectsAPIConfig(SingletonModel):
    """
    global configuration and defaults
    """

    objects_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Objects API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=True,
        related_name="+",
    )
    drc_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Documenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        null=True,
        related_name="+",
    )

    # Overridable defaults
    objecttype = models.URLField(
        _("objecttype"),
        max_length=1000,
        blank=True,
        help_text=_(
            "Default URL of the ProductAanvraag OBJECTTYPE in the Objecttypes API. "
            "The objecttype should have the following three attributes: "
            "1) submission_id; "
            "2) type (the type of productaanvraag); "
            "3) data (the submitted form data)"
        ),
    )
    objecttype_version = models.IntegerField(
        _("objecttype version"),
        null=True,
        blank=True,
        help_text=_("Default version of the OBJECTTYPE in the Objecttypes API"),
    )
    productaanvraag_type = models.CharField(
        _("Productaanvraag type"),
        help_text=_("The type of ProductAanvraag"),
        blank=True,
        max_length=255,
    )
    informatieobjecttype_submission_report = models.URLField(
        _("submission report informatieobjecttype"),
        max_length=1000,
        blank=True,
        help_text=_(
            "Default URL of the INFORMATIEOBJECTTYPE for the submission "
            "report in the Catalogi API"
        ),
    )
    informatieobjecttype_attachment = models.URLField(
        _("attachment informatieobjecttype"),
        max_length=1000,
        blank=True,
        help_text=_(
            "Default URL of the INFORMATIEOBJECTTYPE for the submission "
            "attachments in the Catalogi API"
        ),
    )
    organisatie_rsin = models.CharField(
        _("organisation RSIN"),
        max_length=9,
        blank=True,
        validators=[validate_rsin],
        help_text=_("Default RSIN of organization, which creates the INFORMATIEOBJECT"),
    )

    class Meta:
        verbose_name = _("Objects API configuration")

    def apply_defaults_to(self, options):
        options.setdefault("objecttype", self.objecttype)
        options.setdefault("objecttype_version", self.objecttype_version)
        options.setdefault("productaanvraag_type", self.productaanvraag_type)
        options.setdefault(
            "informatieobjecttype_submission_report",
            self.informatieobjecttype_submission_report,
        )
        options.setdefault(
            "informatieobjecttype_attachment", self.informatieobjecttype_attachment
        )
        options.setdefault("organisatie_rsin", self.organisatie_rsin)
