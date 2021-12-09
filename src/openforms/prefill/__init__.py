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
"""
import logging
from copy import deepcopy
from itertools import groupby
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from zgw_consumers.concurrent import parallel

from openforms.logging import logevent
from openforms.typing import JSONObject

if TYPE_CHECKING:  # pragma: nocover
    from openforms.submissions.models import Submission

default_app_config = "openforms.prefill.apps.PrefillConfig"

logger = logging.getLogger(__name__)


def apply_prefill(configuration: JSONObject, submission: "Submission", register=None):
    """
    Takes a Formiojs definition and invokes all the pre-fill plugins.

    The entire form definition is parsed, plugins and their attributes are extracted
    and each plugin is invoked with the list of attributes (in parallel). If a default
    value was specified for a component, and the prefill plugin returns a value as well,
    the prefill value overrides the default.

    :param configuration: The formiojs form configuration, including all the components.
      This must adhere to the formiojs proprietary JSON schema.
    :param submission: the relevant for submission session, holding the optional BSN or
      other identifying details obtained after authentication. This object is passed
      down to the plugins so that they can inspect the submission context to retrieve
      prefill data.
    :param register: A :class:`openforms.prefill.registry.Registry` instance, holding
      the registered plugins. Defaults to the default registry, but can be specified for
      dependency injection purposes in tests.
    :return: Returns a mutated copy of the configuration, where components
      ``defaultValue`` is set to the value from prefill plugins where possible. If the
      ``defaultValue`` was set through the form builder, it may be overridden by the
      prefill plugin value (if it's not ``None``).
    """
    from .registry import register as default_register

    register = register or default_register

    fields = _extract_prefill_fields(configuration)
    grouped_fields = _group_prefills_by_plugin(fields)

    def invoke_plugin(item: Tuple[str, List[str]]) -> Tuple[str, Dict[str, Any]]:
        plugin_id, fields = item
        plugin = register[plugin_id]

        try:
            values = plugin.get_prefill_values(submission, fields)
        except Exception as e:
            logevent.prefill_retrieve_failure(submission, plugin, e)
            raise
        else:
            logevent.prefill_retrieve_success(submission, plugin, fields)

        return (plugin_id, values)

    with parallel() as executor:
        results = executor.map(invoke_plugin, grouped_fields.items())

    # process the pre-fill results and fill them out
    prefilled_values: Dict[str, Dict[str, Any]] = dict(results)

    # finally, ensure the ``defaultValue`` is set based on prefill results
    config_copy = deepcopy(configuration)
    _set_default_values(config_copy, prefilled_values)
    return config_copy


def _extract_prefill_fields(configuration: JSONObject) -> List[Dict[str, str]]:
    prefills = []
    components = configuration.get("components", [])

    for component in components:
        if prefill := component.get("prefill"):
            if prefill.get("plugin"):
                prefills.append(prefill)
        else:
            nested = _extract_prefill_fields(component)
            prefills += nested

    return prefills


def _group_prefills_by_plugin(fields: List[JSONObject]) -> Dict[str, list]:
    grouper = {}

    def keyfunc(item):
        return item.get("plugin", "")

    sorted_fields = sorted(fields, key=keyfunc)
    for group, _fields in groupby(sorted_fields, key=keyfunc):
        grouper[group] = [field["attribute"] for field in _fields]
    return grouper


def _set_default_values(
    configuration: JSONObject, prefilled_values: Dict[str, Dict[str, Any]]
) -> None:
    """
    Mutates each component found in configuration according to the prefilled values.

    :param configuration: The Formiojs JSON schema describing an entire form or an
      individual component within the form.
    :param prefilled_values: A dict keyed by plugin ID, with values a dict keyed by the
      attribute ID. The value of each attribute key is the prefill value as retrieved.

    This function recurses to deal with the nested component structure. Each component
    is inspected for prefill configuration, which is then looked up in
    ``prefilled_values`` to set the component ``defaultValue``.
    """
    if "prefill" in configuration:
        default_value = configuration.get("defaultValue")
        prefill_value = prefilled_values.get(
            configuration["prefill"]["plugin"], {}
        ).get(configuration["prefill"]["attribute"])

        if prefill_value is None:
            logger.debug(
                "Prefill value for component %s is None, skipping.", configuration["id"]
            )
            return

        if prefill_value != default_value and default_value is not None:
            logger.info(
                "Overwriting non-null default value for component %s",
                configuration["id"],
            )
        configuration["defaultValue"] = prefill_value

    if components := configuration.get("components"):
        for component in components:
            _set_default_values(component, prefilled_values)
