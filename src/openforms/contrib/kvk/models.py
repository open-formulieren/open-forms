from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class KVKConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("_service", "_profiles")


class KVKConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    _service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("KvK API Zoeken"),
        help_text=_("API used for validation of KvK, RSIN and vestigingsnummer's"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    _profiles = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("KvK API Basisprofiel"),
        help_text=_("API used to retrieve basis profielen"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    objects = KVKConfigManager()

    class Meta:
        verbose_name = _("KvK configuration")

    # FIXME: Patch ZGW Consumer behaviour to allow for 2 KvK API's.
    #
    # The KvK uses a single API root path to serve 2 API's. They differ in path
    # but the path is included in the schema and thus is added automatically by
    # ZGW Consumer. You cannot store 2 API's with the same API root, and adding
    # their API base path causes the API base path to be duplicated in
    # requests.

    @property
    def service(self):
        s = self._service
        s.api_root = s.api_root.replace("/v1/zoeken", "")
        return s

    @property
    def profiles(self):
        p = self._profiles
        p.api_root = p.api_root.replace("/v1/basisprofielen", "")
        return p
