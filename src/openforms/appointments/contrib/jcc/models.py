from django.db import models
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from solo.models import SingletonModel

from stuf.managers import ConfigManager

from .constants import CustomerFields

customer_field_choices_without_last_name = (
    choice
    for choice in CustomerFields.choices
    if choice[0] != CustomerFields.last_name.value
)


class JccConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    service = models.OneToOneField(
        "soap.SoapService",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )

    required_customer_fields = ArrayField(
        models.CharField(
            max_length=50, choices=customer_field_choices_without_last_name
        ),
        verbose_name=_("Override JCC optional fields"),
        help_text=_(
            "Preferably, customer fields should be marked as required in JCC. However, "
            "if that is not an option, you can add fields here to mark as required. "
            "Note that you can only mark optional fields as required, not the other "
            "way around."
        ),
        default=list,
        blank=True,
    )

    objects = ConfigManager()

    class Meta:
        verbose_name = _("JCC configuration")
