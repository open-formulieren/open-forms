import uuid as _uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from ordered_model.models import OrderedModel


class FormLogic(OrderedModel):
    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    form = models.ForeignKey(
        to="forms.Form",
        on_delete=models.CASCADE,
        help_text=_("Form to which the JSON logic applies."),
    )
    json_logic_trigger = models.JSONField(
        verbose_name=_("JSON logic"),
        help_text=_("JSON logic associated with a step in a form."),
    )
    actions = models.JSONField(
        verbose_name=_("actions"),
        help_text=_("Which action(s) to perform if the JSON logic evaluates to true."),
    )
    is_advanced = models.BooleanField(
        verbose_name=_("is advanced"),
        help_text=_(
            "Is this an advanced rule (the admin user manually wrote the trigger as JSON)?"
        ),
        default=False,
    )

    order_with_respect_to = "form"

    class Meta(OrderedModel.Meta):
        pass
