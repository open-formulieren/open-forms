import uuid as _uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from ordered_model.models import OrderedModel


class FormLogic(OrderedModel):
    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    description = models.CharField(
        _("description"),
        max_length=100,
        blank=True,
        help_text=_("Logic rule description in natural language."),
    )
    form = models.ForeignKey(
        to="forms.Form",
        on_delete=models.CASCADE,
        help_text=_("Form to which the JSON logic applies."),
    )
    trigger_from_step = models.ForeignKey(
        "FormStep",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("trigger from step"),
        help_text=_(
            "When set, the trigger will only be checked once the specified step is reached. "
            "This means the rule will never trigger for steps before the specified trigger step. "
            "If unset, the trigger will always be checked."
        ),
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
        verbose_name = _("form logic")
        verbose_name_plural = _("form logic rules")

    def clean(self):
        super().clean()

        if (
            self.trigger_from_step
            and self.form
            and self.trigger_from_step.form != self.form
        ):
            raise ValidationError(
                _(
                    "You must specify a step that belongs to the same form as the logic rule itself."
                ),
                code="invalid",
            )

    @property
    def action_operations(self):
        from openforms.submissions.logic.actions import compile_action_operation

        for action in map(compile_action_operation, self.actions):
            action.rule = self
            yield action

    @property
    def hidden_actions(self):
        """Generator which yields actions that change the "hidden" property."""
        from openforms.submissions.logic.actions import (
            PropertyAction,
            compile_action_operation,
        )

        for action in map(compile_action_operation, self.actions):
            if not isinstance(action, PropertyAction) or action.property != "hidden":
                continue

            action.rule = self
            yield action
