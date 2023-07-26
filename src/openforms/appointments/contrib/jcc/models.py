from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from openforms.utils.validators import validate_service_url_not_empty
from stuf.managers import ConfigManager


class JccConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    service = models.OneToOneField(
        "soap.SoapService",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        validators=[validate_service_url_not_empty],
    )

    objects = ConfigManager()

    class Meta:
        verbose_name = _("JCC configuration")
