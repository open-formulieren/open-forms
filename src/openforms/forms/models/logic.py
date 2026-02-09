import uuid as _uuid
from collections.abc import Collection

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from ordered_model.models import OrderedModel

from openforms.forms.models import FormStep
from openforms.utils.json_logic import introspect_json_logic
from openforms.variables.service import resolve_key


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
    _steps: set[FormStep] | None = None

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
        from openforms.submissions.logic.actions import PropertyAction

        for action in self.action_operations:
            if (
                not isinstance(action, PropertyAction)
                or action.property_name != "hidden"
            ):
                continue
            yield action

    @property
    def components_in_hidden_actions(self) -> set[str]:
        """Set of components for which an action changes the "hidden" property."""
        return {action.component for action in self.hidden_actions}

    @property
    def unresolved_input_variables_from_trigger(self) -> set[str]:
        """Set of unresolved input variables from the JSON logic trigger."""
        return {
            var.key
            for var in introspect_json_logic(self.json_logic_trigger).get_input_keys()
        }

    @property
    def steps(self) -> set[FormStep]:
        """
        Set of steps (determined by the actions) on which this rule should be executed.
        """
        if self._steps is not None:
            return self._steps

        self._steps = set()
        for action in self.action_operations:
            self._steps |= action.steps

        return self._steps

    @property
    def input_variable_keys(self) -> Collection[str]:
        """
        Set of input form variable keys, determined from the JSON logic trigger and all
        actions.
        """
        raw_input_keys = self.unresolved_input_variables_from_trigger
        for action in self.action_operations:
            raw_input_keys |= action.unresolved_input_variables

        return {
            resolved_key
            for key in raw_input_keys
            if (resolved_key := resolve_key(key, self.form.all_form_variable_keys))
            is not None
        }

    @property
    def output_variable_keys(self) -> Collection[str]:
        """Set of output form variable keys, determined from all actions."""
        raw_output_keys = set()
        for action in self.action_operations:
            raw_output_keys |= action.unresolved_output_variables

        # Resolving the key here should not be necessary, as we do not support changing
        # values inside editgrid items (and also selectboxes, partners, children), so
        # it should already be the top-level key. We do need to do the check on all
        # form variables, as they might still include components for which we don't have
        # a variable (e.g. layout components).
        return {
            key for key in raw_output_keys if key in self.form.all_form_variable_keys
        }
