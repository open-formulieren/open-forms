from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class KVKConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "profile_service",
            "profile_service__client_certificate",
            "profile_service__server_certificate",
            "branch_profile_service",
            "branch_profile_service__client_certificate",
            "branch_profile_service__server_certificate",
            "search_service",
            "search_service__client_certificate",
            "search_service__server_certificate",
        )


class KVKConfig(SingletonModel):
    """
    Global configuration and defaults.
    """

    profile_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("KvK API Basisprofiel"),
        help_text=_("Service for API used to retrieve basis profielen."),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )
    branch_profile_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("KvK API Vestigingsprofiel"),
        help_text=_("Service for API used to retrieve vestingings profielen."),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )
    search_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("KvK API Zoeken"),
        help_text=_(
            "Service for API used for validation of KvK, RSIN and vestigingsnummer's."
        ),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    objects = KVKConfigManager()

    class Meta:
        verbose_name = _("KvK configuration")
