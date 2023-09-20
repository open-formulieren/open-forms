from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class BAGConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "bag_service",
            "bag_service__client_certificate",
            "bag_service__server_certificate",
        )


class BAGConfig(SingletonModel):
    bag_service = models.ForeignKey(
        "zgw_consumers.Service",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("BAG service"),
        limit_choices_to={"api_type": APITypes.orc},
        help_text=_("Select which service to use for the BAG API."),
    )

    objects = BAGConfigManager()

    class Meta:
        verbose_name = _("BAG configuration")
