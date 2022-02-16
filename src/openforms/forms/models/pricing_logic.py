import uuid as _uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class FormPriceLogic(models.Model):
    """
    Express dynamic pricing using form logic.

    By default, prices are encapsulated in :class:`openforms.products.models.Product`,
    but certain form conditions can lead to modified prices.

    We leverage json-logic rules to evaluate conditions and specify prices when a
    condition evaluates to ``True``.

    The data model is similar to :class:`openforms.forms.models.FormLogic`.

    .. todo::

       Document logic evaluation - rules are evaluated and as soon as one matches,
       that's the winner. If multiple rules match, the first one wins.

    .. todo::

       Support complex conditions (AND/OR them together). This is a broader logic
       editing/evaluation issue that applies for regular form logic too.
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    form = models.ForeignKey(
        to="Form",
        on_delete=models.CASCADE,
        help_text=_("Form to which the pricing JSON logic applies."),
    )
    json_logic_trigger = models.JSONField(
        verbose_name=_("JSON logic"),
        help_text=_(
            'JSON logic expression that must evaluate to "true" for the price '
            "to apply."
        ),
    )
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("form price rule")
        verbose_name_plural = _("form price rules")
