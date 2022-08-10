"""
This package holds the base module structure for the pre-fill plugins used in Open Forms.

Various sources exist that can be consulted to fetch data for an active session,
where the BSN, CoC number... can be used to retrieve this data. Think of pre-filling
the address details of a person after logging in with DigiD.

The package integrates with the form builder such that it's possible for every form
field to select which pre-fill plugin to use and which value to use from the fetched
result. Plugins can be registered using a similar approach to the registrations
package. Each plugin is responsible for exposing which attributes/data fragments are
available, and for performing the actual look-up. Plugins receive the
:class:`openforms.submissions.models.Submission` instance that represents the current
form session of an end-user.

Prefill values are embedded as default values for form fields, dynamically for every
user session using the component rewrite functionality in the serializers.

So, to recap:

1. Plugins are defined and registered
2. When editing form definitions in the admin, content editors can opt-in to pre-fill
   functionality. They select the desired plugin, and then the desired attribute from
   that plugin.
3. End-user starts the form and logs in, thereby creating a session/``Submission``
4. The submission-specific form definition configuration is enhanced with the pre-filled
   form field default values.

.. todo:: Move the public API into ``openforms.prefill.service``.

"""
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import elasticapm
from glom import Path, PathAccessError, glom
from zgw_consumers.concurrent import parallel

from openforms.formio.utils import format_date_value, iter_components
from openforms.logging import logevent
from openforms.plugins.exceptions import PluginNotEnabled
from openforms.submissions.constants import SubmissionValueVariableSources
from openforms.typing import JSONObject

if TYPE_CHECKING:  # pragma: nocover
    from openforms.submissions.models import Submission

logger = logging.getLogger(__name__)


@elasticapm.capture_span(span_type="app.prefill")
def _fetch_prefill_values(
    grouped_fields: Dict[str, list], submission: "Submission", register
) -> Dict[str, Dict[str, Any]]:
    @elasticapm.capture_span(span_type="app.prefill")
    def invoke_plugin(item: Tuple[str, List[str]]) -> Tuple[str, Dict[str, Any]]:
        plugin_id, fields = item
        plugin = register[plugin_id]

        if not plugin.is_enabled:
            raise PluginNotEnabled()

        try:
            values = plugin.get_prefill_values(submission, fields)
        except Exception as e:
            logger.exception(f"exception in prefill plugin '{plugin_id}'")
            logevent.prefill_retrieve_failure(submission, plugin, e)
            return plugin_id, {}
        else:
            logevent.prefill_retrieve_success(submission, plugin, fields)
            return plugin_id, values

    with parallel() as executor:
        results = executor.map(invoke_plugin, grouped_fields.items())

    return dict(results)


def _set_default_values(
    configuration: JSONObject, prefilled_values: Dict[str, Any]
) -> None:
    """
    Mutates each component found in configuration according to the prefilled values.

    :param configuration: The Formiojs JSON schema describing an entire form or an
      individual component within the form.
    :param prefilled_values: A dict keyed by component key, with values the value fetched
    from the prefill calls (from :func:`prefill_variables`).

    Each component is inspected for prefill configuration, after which the value is
    looked up in ``prefilled_values``.
    """
    from openforms.formio.service import normalize_value_for_component

    for component in iter_components(configuration, recursive=True):
        if not (component_key := component.get("key")):
            continue
        if not (prefill := component.get("prefill")):
            continue
        if not prefill.get("plugin"):
            continue
        if not prefill.get("attribute"):
            continue

        default_value = component.get("defaultValue")
        prefill_value = prefilled_values.get(component_key)

        if prefill_value is None:
            logger.debug("Prefill value for component %r is None, skipping.", component)
            continue

        # 1693: we need to normalize values according to the format expected by the
        # component. For example, (some) prefill plugins return postal codes without
        # space between the digits and the letters.
        prefill_value = normalize_value_for_component(component, prefill_value)

        if prefill_value != default_value and default_value is not None:
            logger.info(
                "Overwriting non-null default value for component %r",
                component,
            )

        component["defaultValue"] = prefill_value
        if component["type"] == "date":
            component["defaultValue"] = format_date_value(prefill_value)


def inject_prefill(configuration: dict, submission: "Submission") -> None:
    _set_default_values(configuration, submission.get_prefilled_data())


@elasticapm.capture_span(span_type="app.prefill")
def prefill_variables(submission: "Submission", register=None) -> None:
    from openforms.submissions.models import SubmissionValueVariable

    from .registry import register as default_register

    register = register or default_register

    state = submission.load_submission_value_variables_state()

    grouped_fields = {}
    variables_to_prefill = []
    for key, submission_value_variable in state.variables.items():
        prefill_plugin = submission_value_variable.form_variable.prefill_plugin
        if prefill_plugin == "":
            continue

        if prefill_plugin in grouped_fields:
            grouped_fields[prefill_plugin] += [
                submission_value_variable.form_variable.prefill_attribute
            ]
        else:
            grouped_fields[prefill_plugin] = [
                submission_value_variable.form_variable.prefill_attribute
            ]

        variables_to_prefill.append(submission_value_variable)

    results = _fetch_prefill_values(grouped_fields, submission, register)

    for variable in variables_to_prefill:
        try:
            prefill_value = glom(
                results,
                Path(
                    variable.form_variable.prefill_plugin,
                    variable.form_variable.prefill_attribute,
                ),
            )
        except PathAccessError:
            continue

        variable.value = prefill_value
        variable.source = SubmissionValueVariableSources.prefill

    # Prefill variables is invoked once at the beginning od the submission, so no need to worry about updates
    SubmissionValueVariable.objects.bulk_create(variables_to_prefill)
