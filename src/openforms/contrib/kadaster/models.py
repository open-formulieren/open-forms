from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from openforms.pre_requests.clients import PreRequestZGWClient


def get_default_search_service():
    default_service, _ = Service.objects.get_or_create(
        api_root="https://api.pdok.nl/bzk/locatieserver/search/",
        defaults={
            "api_type": APITypes.orc,
            "label": "PDOK locatieserver",
            "oas": "https://api.pdok.nl/bzk/locatieserver/search/v3_1/openapi.json",
            "auth_type": AuthTypes.no_auth,
        },
    )
    return default_service


class KadasterApiConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("search_service")


class KadasterApiConfig(SingletonModel):
    """
    Global configuration and defaults.
    """

    search_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Kadaster API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        default=get_default_search_service,
    )

    objects = KadasterApiConfigManager()

    class Meta:
        verbose_name = _("Kadaster API configuration")

    def get_client(self) -> PreRequestZGWClient:
        client = self.search_service.build_client()
        assert isinstance(client, PreRequestZGWClient)
        # the OpenAPI spec does not use any semantic suffixes
        client.operation_suffix_mapping = {
            "list": "",
            "retrieve": "",
            "create": "",
            "update": "",
            "partial_update": "",
            "delete": "",
        }
        return client
