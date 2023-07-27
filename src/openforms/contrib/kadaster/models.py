from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service


def get_default_kadaster_service():
    default_service = Service.objects.create(
        label="Locatieserver",
        api_type=APITypes.orc,
        api_root="https://api.pdok.nl/bzk/locatieserver/search/",
        oas="https://api.pdok.nl/bzk/locatieserver/search/v3_1/openapi.json",
        auth_type=AuthTypes.no_auth,
    )
    return default_service


class KadasterApiConfig(SingletonModel):
    """
    global configuration and defaults
    """

    kadaster_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Kadaster API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        null=True,
        related_name="+",
        default=get_default_kadaster_service,
    )

    class Meta:
        verbose_name = _("Kadaster API configuration")
