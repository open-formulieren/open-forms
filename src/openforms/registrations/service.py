from openforms.formio.typing import Component
from openforms.submissions.models import Submission
from openforms.typing import JSONObject

from .base import BasePlugin
from .registry import register as registry

__all__ = [
    "get_registration_plugin",
    "plugin_allows_json_schema_generation",
    "process_variable_schema",
]


class InvalidBackendIdError(Exception):
    pass


def get_registration_plugin(submission: Submission) -> BasePlugin | None:
    backend = submission.registration_backend

    if not backend:
        return

    registry_ = backend._meta.get_field("backend").registry
    return registry_[backend.backend]


def plugin_allows_json_schema_generation(backend: str, options: dict) -> bool:
    """
    Indicate whether the plugin allows generating a JSON schema.

    :param backend: The backend identifier.
    :param options: Backend options.
    """
    try:
        plugin = registry[backend]
    except KeyError:
        raise InvalidBackendIdError(f"No plugin found for backend id: {backend}")

    return plugin.allows_json_schema_generation(options)


def process_variable_schema(
    component: Component, schema: JSONObject, backend_id: str, backend_options: dict
):
    """Process a variable schema according to the given registration backend.

    :param component: Formio component configuration of the variable.
    :param schema: JSON schema of the variable.
    :param backend_id: Backend identifier.
    :param backend_options: Backend options. Note: there is no check to ensure the
      options are valid and correspond to the provided ``backend_id``, so please ensure
      that they do.
    """
    try:
        plugin = registry[backend_id]
    except KeyError:
        raise InvalidBackendIdError(f"No plugin found for backend id: {backend_id}")

    if not plugin.allows_json_schema_generation(backend_options):
        raise InvalidBackendIdError(
            f"Processing a variable schema for registration backend '{backend_id}' is "
            f"not implemented."
        )

    plugin.process_variable_schema(component, schema, backend_options)
