import uuid as _uuid
from functools import cached_property

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from ordered_model.models import OrderedModel

from openforms.forms.models import FormStep
from openforms.utils.json_logic import introspect_json_logic


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
        help_text=_("List of form steps on which this logic rule should be executed."),
        blank=True,
        related_name="logic_rules",
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
        from openforms.submissions.logic.actions import PropertyAction

        for action in self.action_operations:
            if not isinstance(action, PropertyAction) or action.property != "hidden":
                continue
            yield action

    @property
    def components_in_hidden_actions(self) -> set[str]:
        """Set of components for which an action changes the "hidden" property."""
        return {action.component for action in self.hidden_actions}

    # @property
    # def input_steps(self):
    #     return {
    #         form_step for key in self.input_variable_keys
    #         if (form_step := self.form.get_form_step(key)) is not None
    #     }
    #
    # @property
    # def output_steps(self):
    #     return {
    #         form_step for key in self.output_variable_keys
    #         if (form_step := self.form.get_form_step(key)) is not None
    #     }

    @property
    def steps(self) -> set[FormStep]:
        if getattr(self, "_steps", None) is not None:
            return self._steps

        from openforms.variables.service import get_static_variables

        all_form_vars = {
            *[var_.key for var_ in get_static_variables()],
            *[var_.key for var_ in self.form.formvariable_set.all()],
        }

        raw_input_keys = {
            var_.key
            for var_ in introspect_json_logic(self.json_logic_trigger).get_input_keys()
        }

        self._steps = set()
        for action in self.action_operations:
            self._steps |= action.get_steps(raw_input_keys, all_form_vars)

        return self._steps

    # TODO-2409: perhaps rename to `determine_steps_from_graph(graph: DiGraph)`?
    @steps.setter
    def steps(self, v: set[FormStep]):
        # We cannot determine a step if both the input and output variables are
        # user-defined. In this case, we need to manually check the predecessors of this
        # logic rule in the graph, determine a step from them, and set it to the rule.
        self._steps = v

    @cached_property
    def input_variable_keys(self) -> set[str]:
        from openforms.variables.service import get_static_variables

        raw_input_keys = {
            var_.key
            for var_ in introspect_json_logic(self.json_logic_trigger).get_input_keys()
        }
        for action in self.action_operations:
            raw_input_keys |= action.input_variables

        # TODO-2409: is this cached already when evaluating all logic rules of a form
        #  one after another? If not, can this be cached on the form? Getting the form
        #  variable set for all logic rules one in succession will be expensive. When
        #  iterating over the form logic objects, use a
        #  `prefetch_related("form__formvariable_set")` maybe?
        all_form_vars = {
            *[var_.key for var_ in get_static_variables()],
            *[var_.key for var_ in self.form.formvariable_set.all()],
        }

        return {
            resolved_key
            for key in raw_input_keys
            if (resolved_key := _resolve_key(key, all_form_vars)) is not None
        }

    @cached_property
    def output_variable_keys(self) -> set[str]:
        from openforms.variables.service import get_static_variables

        raw_output_keys = set()
        for action in self.action_operations:
            raw_output_keys |= action.output_variables

        all_form_vars = {
            *[var_.key for var_ in get_static_variables()],
            *[var_.key for var_ in self.form.formvariable_set.all()],
        }

        # TODO-2409: resolving the key here should not be necessary, as we do not
        #  support changing values inside editgrids items (probably also
        #  selectboxes, partners, children), so it should already be the top-level
        #  key. We do need to do the check on all form variables, as they might still
        #  include components for which we don't have a variable (e.g. layout
        #  components)
        return {key for key in raw_output_keys if key in all_form_vars}


# TODO-2409: move this to the form/form step/form definition/formio configuration wrapper?
def _resolve_key(input_key: str, all_form_variable_keys: set[str]) -> str | None:
    """Resolve a JSON logic variable key to its corresponding form variable key."""
    # there is a variable with this exact key, it is a valid reference
    if input_key in all_form_variable_keys:
        return input_key

    # TODO-2409: there is an edge case if any of these components include a dot in their
    #  key (this is also broken in the detection for the digest email it seems).
    # Process nested paths (editgrid, selectboxes, partners, children). Note that this
    # doesn't include other nested fields anymore, e.g. a textfield component with key
    # "foo.bar" will have already been resolved.
    outer, *nested = input_key.split(".")

    if outer in all_form_variable_keys:
        return outer

    # If the outer key also doesn't exist, we cannot resolve the complete key, so we
    # just return `None`. Note that the digest email should notify the user of invalid
    # logic rules
    return None
