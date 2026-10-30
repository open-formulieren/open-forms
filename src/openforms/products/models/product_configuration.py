from django.db import models
from django.utils.translation import gettext_lazy as _

from django_jsonform.models.fields import ArrayField
from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class ProductConfigurationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("open_product_service")


class ProductConfiguration(SingletonModel):
    open_product_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Open Product API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type__in": [APITypes.pc, APITypes.ptc]},
        related_name="+",
        null=True,
        help_text=_("Select a Product or Product type Service."),
    )
    content_labels = ArrayField(
        models.CharField(max_length=1000),
        verbose_name=_("Labels to filter product type's content"),
        blank=True,
        default=list,
        help_text=_(
            "Provide a list of existing labels to use/filter when retrieving product "
            "type's content."
        ),
    )

    objects = ProductConfigurationManager()

    class Meta:
        verbose_name = _("product api configuration")
        verbose_name_plural = _("product api configuration")
