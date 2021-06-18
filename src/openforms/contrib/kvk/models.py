from django.db import models
from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices
from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class KVKConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class CompanyOperationChoice(DjangoChoices):
    production = ChoiceItem("Companies_GetCompaniesExtendedV2", _("Production"))
    development = ChoiceItem("CompaniesTest_GetCompaniesExtendedV2", _("Development"))


class KVKConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("KvK API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    use_operation = models.CharField(
        _("KVK Environment"),
        max_length=255,
        default=CompanyOperationChoice.development,
        choices=CompanyOperationChoice.choices,
        help_text=_("The development API uses different paths/operations"),
    )

    objects = KVKConfigManager()

    class Meta:
        verbose_name = _("KvK configuration")
