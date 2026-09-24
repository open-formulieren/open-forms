from copy import deepcopy

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from .constants import FIELD_TO_FORMIO_COMPONENT


def get_default_components():
    components = []
    for component in deepcopy(FIELD_TO_FORMIO_COMPONENT).values():
        # msgspec can't handle lazy translatable strings
        component["label"] = force_str(component["label"])
        if component["type"] == "radio":
            component["values"] = [  # pyright: ignore
                {**option, "label": force_str(option["label"])}
                for option in component["values"]  # pyright: ignore
            ]
        components.append(component)

    return {"components": components}


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
