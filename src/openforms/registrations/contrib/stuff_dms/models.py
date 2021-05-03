from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class StufDMSConfig(SingletonModel):
    """
    global configuration and defaults
    """

    # todo___dms_service = models.ForeignKey(
    #     "zgw_consumers.Service",
    #     on_delete=models.PROTECT,
    #     # limit_choices_to={"api_type": APITypes.zrc},
    #     related_name="zgw_zrc_config",
    #     null=True,
    # )

    def apply_defaults_to(self, options):
        # options.setdefault("xyzzzzz", self.zaaktype)
        pass
