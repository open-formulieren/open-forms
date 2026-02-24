from collections import defaultdict
from collections.abc import Collection, Mapping
from typing import TYPE_CHECKING, ClassVar

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from ..constants import CSPDirective

type AsDictResult = Mapping[str, Collection[str]]


class CSPSettingQuerySet(models.QuerySet):
    def as_dict(self) -> AsDictResult:
        ret = defaultdict(set)
        for directive, value in self.values_list("directive", "value"):
            ret[directive].add(value)
        return {k: list(v) for k, v in ret.items()}


class CSPSettingManager(models.Manager.from_queryset(CSPSettingQuerySet)):
    @transaction.atomic
    def set_for(
        self,
        obj: models.Model,
        settings: list[tuple[CSPDirective, str]],
        identifier: str = "",
    ) -> None:
        """
        Deletes all the connected CSP settings and creates new ones based on the new provided data.

        :param obj: The configuration model providing this CSP entry.
        :param settings: A two-tuple containing values used to create the underlying ``CSPSetting`` model.
        :param identifier: An optional string to further identify the source of this CSP entry.
        """
        instances = [
            CSPSetting(
                content_object=obj,
                directive=directive,
                value=value,
                identifier=identifier,
            )
            for directive, value in settings
        ]

        content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False)
        CSPSetting.objects.filter(
            content_type=content_type,
            object_id=str(obj.pk),
            identifier=identifier,
        ).delete()

        self.bulk_create(instances)

    if TYPE_CHECKING:

        def as_dict(self) -> AsDictResult: ...


class CSPSetting(models.Model):
    directive = models.CharField(
        _("directive"),
        max_length=64,
        choices=CSPDirective.choices,
        help_text=_("CSP header directive."),
    )
    value = models.CharField(
        _("value"),
        max_length=255,
        help_text=_("CSP header value."),
    )

    identifier = models.CharField(
        _("identifier"),
        max_length=64,
        blank=True,
        help_text=_("An extra tag for this CSP entry, to identify the exact source."),
    )

    # Generic relation fields (see https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/#generic-relations):
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("content type"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    object_id = models.TextField(
        verbose_name=_("object id"),
        blank=True,
        db_index=True,
    )
    content_object = GenericForeignKey("content_type", "object_id")

    objects: ClassVar[CSPSettingManager] = CSPSettingManager()  # pyright: ignore[reportIncompatibleVariableOverride]

    class Meta:
        ordering = ("directive", "value")

    def __str__(self):
        return f"{self.directive} '{self.value}'"
