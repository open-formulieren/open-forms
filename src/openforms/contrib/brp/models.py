from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class BRPConfig(SingletonModel):
    brp_service = models.ForeignKey(
        "zgw_consumers.Service",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("BRP service"),
        limit_choices_to={"api_type": APITypes.orc},
        help_text=_("Select which service to use for the BRP API."),
    )

    class Meta:
        verbose_name = _("BRP Configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)
