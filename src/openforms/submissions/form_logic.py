from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional
from urllib.parse import quote

from django.utils.functional import empty

import elasticapm
import jq
from json_logic import jsonLogic

from openforms.formio.service import (
    get_dynamic_configuration,
    inject_variables,
    translate_function,
)
from openforms.formio.utils import get_component_empty_value, is_visible_in_frontend
from openforms.forms.models import FormVariable
from openforms.logging import logevent
from openforms.typing import DataMapping, JSONValue
from openforms.variables.models import DataMappingTypes, ServiceFetchConfiguration
from openforms.variables.validators import HeaderValidator

from .logic.actions import PropertyAction
from .logic.datastructures import DataContainer
from .logic.rules import (
    EvaluatedRule,
    get_current_step,
    get_rules_to_evaluate,
    iter_evaluate_rules,
)
from .models.submission_step import DirtyData

if TYPE_CHECKING:  # pragma: no cover
    from .models import Submission, SubmissionStep


@elasticapm.capture_span(span_type="app.submissions.logic")
def evaluate_form_logic(
    submission: "Submission",
    step: "SubmissionStep",
    data: Dict[str, Any],
    dirty=False,
    **context,
) -> Dict[str, Any]:
    """
    Process all the form logic rules and mutate the step configuration if required.

    The form logic evaluation is split up in multiple stages to achieve a deterministic
    output while respecting the ordering of logic rules. The logic evaluation has a
    number of side effects:

    * setting/writing values for variables
    * dynamic Formio configuration updates, based on the variable values
    * dynamic Formio configuration updates, based on the logic actions
    * dynamic Formio configuration based on the request context

    We achieve this by:

    1. Loading the submission and submission step (passed as function arguments)
    2. Prefilled data is saved at submission start and available in the variables
    3. Loading the variable state, which populates non-saved values with their defaults.
    4. Apply any dirty data (unsaved) to the variable state
    5. Evaluate the logic rules in order, for each action in each triggered rule:

       1. If a variable value is being update, update the variable state
       2. Else record the action to perform to the configuration (but don't apply it yet!)

    6. The variables state is now completely resolved and can be used as input for the
       dynamic configuration.
    7. Apply the dynamic configuration

       1. Apply the component property mutations that were recorded in 5.
       2. Interpolate the component configuration with the variables.
       3. Handle custom formio types (which require variables as input!)

    """
    # grab the configuration that will be mutated
    config_wrapper = step.form_step.form_definition.configuration_wrapper
    # 1. we have `submission` and `step` available and ...
    # 2. the prefilled variables are already recorded in the variables state
    #
    # The Formio *default values* are also recorded in here, because the `FormVariable`
    # for each component derives that from the configuration at save-time.
    #
    if not step.data:
        step.data = DirtyData({})

    # ensure this function is idempotent
    _evaluated = getattr(step, "_form_logic_evaluated", False)
    if _evaluated:
        return config_wrapper.configuration

    # 3. Load the (variables) state
    submission_variables_state = submission.load_submission_value_variables_state()

    # 4. Apply the (dirty) data to the variable state.
    submission_variables_state.set_values(data)

    rules = get_rules_to_evaluate(submission, step)
    data_container = DataContainer(state=submission_variables_state)

    # 5. Evaluate the logic rules in order
    mutation_operations = []
    evaluated_rules: List[EvaluatedRule] = []

    # 5.1 - if the action type is to set a variable, update the variable state. This
    # happens inside of iter_evaluate_rules. This is the ONLY operation that is allowed
    # to execute while we're looping through the rules.
    with elasticapm.capture_span(
        name="collect_logic_operations", span_type="app.submissions.logic"
    ):
        for operation in iter_evaluate_rules(
            rules, data_container, on_rule_check=evaluated_rules.append
        ):
            mutation_operations.append(operation)

    # 6. The variable state is now completely resolved - we can start processing the
    # dynamic configuration and side effects.

    # Calculate which data has changed from the initial, for the step.
    updated_step_data = data_container.get_updated_step_data(step)
    step.data = DirtyData(updated_step_data)

    # 7. finally, apply the dynamic configuration

    # we need to apply the context-specific configurations before we can apply
    # mutations based on logic, which is then in turn passed to the serializer(s)
    # TODO: refactor this to rely on variables state
    config_wrapper = get_dynamic_configuration(
        config_wrapper,
        # context is expected to contain request, as it's the default behaviour with
        # DRF view(set)s and serializers.
        # TODO: check if we can use context["request"] rather than .get - None is not
        # expected, but that currently breaks a lot of tests...
        request=context.get("request"),
        submission=submission,
        data=data_container.data,
    )

    # 7.1 Apply the component mutation operations
    for mutation in mutation_operations:
        mutation.apply(step, config_wrapper)

    initial_data = data_container.initial_data

    # XXX: See #2340 and #2409 - we need to clear the values of components that are
    # (eventually) hidden BEFORE we do any further processing. This is only a bandaid
    # fix, as the (stale) data has potentially been input for other logic rules.
    # Note that only the dirty data logic check acts on these differences.

    # only keep the changes in the data, so that old values do not overwrite otherwise
    # debounced client-side data changes
    data_diff = {}
    for component in config_wrapper:
        key = component["key"]
        is_visible = config_wrapper.is_visible_in_frontend(key, data_container.data)
        if is_visible:
            continue

        original_value = initial_data.get(key, empty)
        empty_value = get_component_empty_value(component)
        if original_value is empty or original_value == empty_value:
            continue

        if not component.get("clearOnHide", False):
            continue

        # clear the value
        data_container.update({key: empty_value})
        data_diff[key] = empty_value

    # 7.2 Interpolate the component configuration with the variables.
    translate = (
        # We need to interpolate the translated string
        translate_function(submission, step)
        if (submission.form.translation_enabled and step.form_step)
        else str  # a noop when translation is not enabled
    )
    inject_variables(config_wrapper, data_container.data, translate)

    # 7.3 Handle custom formio types - TODO: this needs to be lifted out of
    # :func:`get_dynamic_configuration` so that it can use variables.

    # Logging the rules
    logevent.submission_logic_evaluated(
        submission,
        evaluated_rules,
        initial_data,
        data_container.data,
    )

    # process the output for logic checks with dirty data
    if dirty:
        # Iterate over all components instead of `step.data`, to take hidden fields into account (See: #1755)
        for component in config_wrapper:
            key = component["key"]
            # already processed, don't process it again
            if key in data_diff:
                continue

            new_value = updated_step_data.get(key, empty)
            original_value = initial_data.get(key, empty)
            # Reset the value of any field that may have become hidden again after evaluating the logic
            if original_value is not empty and original_value != (
                component_empty_value := get_component_empty_value(component)
            ):
                if (
                    component
                    and not is_visible_in_frontend(component, data_container.data)
                    and component.get("clearOnHide")
                ):
                    data_diff[key] = component_empty_value
                    continue

            if new_value is empty or new_value == original_value:
                continue
            data_diff[key] = new_value

        # only return the 'overrides'
        step.data = DirtyData(data_diff)

    step._form_logic_evaluated = True

    return config_wrapper.configuration


def check_submission_logic(
    submission: "Submission", unsaved_data: Optional[dict] = None
) -> None:
    if getattr(submission, "_form_logic_evaluated", False):
        return

    submission_state = submission.load_execution_state()
    # if there are no form steps at all, then there's nothing to do
    if not submission_state.form_steps:
        return

    step = get_current_step(submission)
    rules = get_rules_to_evaluate(submission)

    # load the data state and all variables
    submission_variables_state = submission.load_submission_value_variables_state()
    if unsaved_data:
        submission_variables_state.set_values(unsaved_data)
    data_container = DataContainer(state=submission_variables_state)

    mutation_operations = []
    for operation in iter_evaluate_rules(rules, data_container):
        # component mutations can be skipped as we're not in the context of a single
        # form step.
        if isinstance(operation, PropertyAction):
            continue
        mutation_operations.append(operation)

    for mutation in mutation_operations:
        mutation.apply(step, {})

    submission._form_logic_evaluated = True


def bind(var: FormVariable, context: DataMapping) -> JSONValue:
    """Bind a value to a variable `var`

    :raises: :class:`requests.HTTPException` for internal server errors
    :raises: :class:`zds_client.client.ClientError` for HTTP 4xx status codes
    :raises: :class:`NotImplementedError` for FormVariable
    """
    fetch_config: ServiceFetchConfiguration | None

    match var:
        case FormVariable(service_fetch_configuration=fetch_config) if fetch_config:
            client = fetch_config.service.build_client()
            request_args = _request_arguments(fetch_config, context)
            raw_value = client.request(**request_args)

            match fetch_config.data_mapping_type, fetch_config.mapping_expression:
                case DataMappingTypes.jq, expression:
                    # XXX raise warning if len(result) > 1 ?
                    value = jq.compile(expression).input(raw_value).first()
                case DataMappingTypes.json_logic, expression:
                    value = jsonLogic(expression, raw_value)
                case _:
                    value = raw_value
        case _:
            raise NotImplementedError()

    return value


def _request_arguments(fetch_config: ServiceFetchConfiguration, context: DataMapping):
    headers = {
        # no leading spaces and the value into the legal field-value codespace
        header: value.format(**context).strip().encode("utf-8").decode("latin1")
        for header, value in (fetch_config.headers or {}).items()
    }
    # before we go further
    # assert headers are still valid after we put submmitter data in there
    HeaderValidator()(headers)

    escaped_values = {k: quote(str(v), safe="") for k, v in context.items()}

    query_params = fetch_config.query_params.format(**escaped_values)
    query_params = query_params[1:] if query_params.startswith("?") else query_params

    request_args = dict(
        path=fetch_config.path.format(**escaped_values),
        params=query_params,
        method=fetch_config.method,
        headers=headers,
        # XXX operationId is a required parameter to zds-client...
        # Maybe offer as alternative to path and method?
        operation="",
    )
    if fetch_config.body is not None:
        request_args["json"] = fetch_config.body
    return request_args
