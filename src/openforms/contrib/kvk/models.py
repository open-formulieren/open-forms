from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class KVKConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "service",
            "service__client_certificate",
            "service__server_certificate",
        )


class KVKConfig(SingletonModel):
    """
    Global configuration and defaults.
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("KvK API"),
        help_text=_("Service for API interaction with the KVK."),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    objects = KVKConfigManager()

    class Meta:
        verbose_name = _("KvK configuration")
