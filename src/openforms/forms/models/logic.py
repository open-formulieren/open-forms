from __future__ import annotations

import uuid as _uuid
from collections import defaultdict
from collections.abc import Collection, Iterator, Mapping
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from ordered_model.models import OrderedModel

from openforms.forms.models import FormStep
from openforms.utils.json_logic import introspect_json_logic
from openforms.variables.service import resolve_key

if TYPE_CHECKING:
    from openforms.submissions.logic.actions import ActionOperation, PropertyAction


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
    form_steps = models.ManyToManyField(
        FormStep,
        verbose_name=_("form steps"),
        help_text=_(
            "Collection of form steps on which this logic rule should be executed."
        ),
        blank=True,
        related_name="logic_rules",
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
    _input_variables_from_action_map: Mapping[str, set[int]] | None = None
    _output_variables_from_action_map: Mapping[str, set[int]] | None = None

    class Meta(OrderedModel.Meta):
        verbose_name = _("form logic")
        verbose_name_plural = _("form logic rules")

    @property
    def action_operations(self) -> Iterator[ActionOperation]:
        from openforms.submissions.logic.actions import compile_action_operation

        for action in map(compile_action_operation, self.actions):
            action.rule = self
            yield action

    @property
    def hidden_actions(self) -> Iterator[PropertyAction]:
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
    def input_variables_from_trigger(self) -> set[str]:
        """Set of resolved input variables from the JSON logic trigger."""
        return {
            resolved_key
            for var in introspect_json_logic(self.json_logic_trigger).get_input_keys()
            if (resolved_key := resolve_key(var.key, self.form.all_form_variable_keys))
            is not None
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

    @steps.setter
    def steps(self, v: set[FormStep]):
        # We cannot determine a step if both the input and output variables are
        # user-defined. In this case, we need to manually check the predecessors of this
        # logic rule in the graph, determine a step from them, and set it to the rule.
        self._steps = v

    @property
    def input_variables_from_action_map(self) -> Mapping[str, set[int]]:
        """
        Mapping from action input variable keys (resolved) to a set of action numbers in
        which they are used.
        """
        if self._input_variables_from_action_map is None:
            self._create_variables_action_maps()
        assert self._input_variables_from_action_map is not None
        return self._input_variables_from_action_map

    @property
    def output_variables_from_action_map(self) -> Mapping[str, set[int]]:
        """
        Mapping from action output variable keys (resolved) to a set of action numbers
        in which they are used.
        """
        if self._output_variables_from_action_map is None:
            self._create_variables_action_maps()
        assert self._output_variables_from_action_map is not None
        return self._output_variables_from_action_map

    def _create_variables_action_maps(self) -> None:
        """
        Create mappings from variable keys (resolved) to a set of action numbers in
        which they are used.
        """
        input_mapping: defaultdict[str, set[int]] = defaultdict(set)
        output_mapping: defaultdict[str, set[int]] = defaultdict(set)
        for i, action in enumerate(self.action_operations):
            # Input variables mapping
            for key in action.unresolved_input_variables:
                resolved_key = resolve_key(key, self.form.all_form_variable_keys)
                if resolved_key is None:
                    continue
                input_mapping[resolved_key].add(i)

            # Output variables mapping
            for key in action.unresolved_output_variables:
                # Resolving the key here should not be necessary, as we do not support
                # changing values inside editgrid items (and also selectboxes, partners,
                # children), so it should already be the top-level key. We do need to do
                # the check on all form variables, as they might still include
                # components for which we don't have a variable (e.g. layout
                # components).
                if key not in self.form.all_form_variable_keys:
                    continue
                output_mapping[key].add(i)

        self._input_variables_from_action_map = input_mapping
        self._output_variables_from_action_map = output_mapping

    @property
    def input_variable_keys(self) -> Collection[str]:
        """
        Collection of input form variable keys, determined from the JSON logic trigger
        and all actions.
        """
        return set(self.input_variables_from_action_map).union(
            self.input_variables_from_trigger
        )

    @property
    def output_variable_keys(self) -> Collection[str]:
        """Collection of output form variable keys, determined from all actions."""
        return set(self.output_variables_from_action_map)

    @property
    def is_backend_logic_evaluation_required(self) -> bool:
        """
        Indicate whether this rule contains any actions that require the backend for
        logic evaluation.

        :return: ``True`` if any action requires backend, ``False`` otherwise.
        """
        return any(
            action.is_backend_logic_evaluation_required
            for action in self.action_operations
        )
