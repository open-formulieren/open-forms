from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service


def get_default_search_service():
    default_service, _ = Service.objects.get_or_create(
        api_root="https://api.pdok.nl/bzk/locatieserver/search/",
        defaults={
            "api_type": APITypes.orc,
            "label": "PDOK locatieserver",
            "auth_type": AuthTypes.no_auth,
        },
    )
    return default_service


class KadasterApiConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "search_service",
            "search_service__client_certificate",
            "search_service__server_certificate",
            "bag_service",
            "bag_service__client_certificate",
            "bag_service__server_certificate",
        )


class KadasterApiConfig(SingletonModel):
    """
    Global configuration and defaults.
    """

    search_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Locatieserver API"),
        help_text=_("Service for geo search queries."),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        default=get_default_search_service,
    )

    bag_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("BAG service"),
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        help_text=_("Select which service to use for the BAG API."),
    )

    objects = KadasterApiConfigManager()

    class Meta:
        verbose_name = _("Kadaster API configuration")
