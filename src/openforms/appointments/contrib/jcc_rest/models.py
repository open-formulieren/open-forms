from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from .constants import FIELD_TO_FORMIO_COMPONENT


def get_default_components():
    return {"components": list(FIELD_TO_FORMIO_COMPONENT.values())}


class JccRestConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class JccRestConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("JCC Rest API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )
    configuration = models.JSONField(
        _("components configuration"),
        default=get_default_components,
        encoder=DjangoJSONEncoder,
        help_text=_("The contact details components as Form.io JSON schema"),
    )

    objects = JccRestConfigManager()

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        verbose_name = _("JCC Rest configuration")
