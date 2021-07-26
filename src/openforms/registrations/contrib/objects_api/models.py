from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


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

    class Meta:
        verbose_name = _("Objects API configuration")

    def apply_defaults_to(self, options):
        options.setdefault("objecttype", self.objecttype)
        options.setdefault("objecttype_version", self.objecttype_version)
        options.setdefault("productaanvraag_type", self.productaanvraag_type)
