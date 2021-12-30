from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from openforms.utils.validators import validate_digits


class StufZDSConfigManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        qs = super().get_queryset()
        return qs.select_related("service")


class StufZDSConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "stuf.StufService",
        on_delete=models.PROTECT,
        related_name="stuf_zds_config",
        null=True,
    )

    gemeentecode = models.CharField(
        _("Municipality code"),
        max_length=4,
        help_text=_("Municipality code to register zaken"),
        validators=[validate_digits],
    )

    objects = StufZDSConfigManager()

    def apply_defaults_to(self, options):
        options.setdefault("gemeentecode", self.gemeentecode)

    def get_client(self, options):
        from .client import StufZDSClient

        return StufZDSClient(self.service, options)

    class Meta:
        verbose_name = _("StUF-ZDS configuration")
