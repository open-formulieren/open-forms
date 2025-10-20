from django.db import models
from django.utils.translation import gettext_lazy as _

from zgw_consumers.constants import APITypes


class CustomerInteractionsAPIGroupConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("customer_interactions_service")


class CustomerInteractionsAPIGroupConfig(models.Model):
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("A recognisable name for this API group"),
    )
    identifier = models.SlugField(
        _("identifier"),
        blank=False,
        null=False,
        unique=True,
        help_text=_("A unique, human-friendly identifier to identify this group."),
    )
    customer_interactions_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Customer Interactions API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.kc},
        related_name="+",
    )

    objects = CustomerInteractionsAPIGroupConfigManager()

    class Meta:
        verbose_name = _("Customer interactions API group")
        verbose_name_plural = _("Customer interactions API groups")

    def __str__(self) -> str:
        return self.name
