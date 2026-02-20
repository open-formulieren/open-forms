from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from openforms.formio.typing import Component

from .constants import FIELD_TO_FORMIO_COMPONENT

type ComponentInputMap = dict[str, list[Component]]
type ComponentOutputMap = dict[str, list[str]]


def resolve_lazy(obj: dict[str, list[Component]]) -> dict[str, list[Component]]:
    """
    Helper function for evaluating lazy objects (translatable fields).
    """
    match obj:
        case dict():
            return {k: resolve_lazy(v) for k, v in obj.items()}  # type: ignore [ReportReturnType]
        case list():
            return [resolve_lazy(v) for v in obj]
        case int():
            return obj
        case _:
            return force_str(obj)


def get_default_components() -> dict[str, list[Component]]:
    """
    Populate the components configuration according to JCC Rest API response for the fields.

    This is done by using the defined components in constants file and only once. The user
    is then responsible to modify (only the translations) of these components via the
    JccRestConfig model in the admin.
    """
    return resolve_lazy({"components": list(FIELD_TO_FORMIO_COMPONENT.values())})


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
        help_text=_("The contact details components as Form.io JSON schema"),
    )

    objects = JccRestConfigManager()

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        verbose_name = _("JCC Rest configuration")
