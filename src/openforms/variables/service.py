"""
Public Python API to access (static) form variables.
"""

from typing import TypedDict

from openforms.forms.models import FormVariable
from openforms.plugins.registry import BaseRegistry
from openforms.registrations.registry import register as registration_plugins_registry
from openforms.submissions.models import Submission
from openforms.typing import StrOrPromise

from .base import BaseStaticVariable
from .registry import register_static_variable as static_variables_registry

__all__ = ["get_static_variables", "get_registration_plugins_variables"]


def get_static_variables(
    *,
    submission: Submission | None = None,
    variables_registry: BaseRegistry[BaseStaticVariable] | None = None,
) -> list[FormVariable]:
    """
    Return the full collection of static variables registered by all apps.

    :param submission: Optional, but recommended - the submission instance to get the
      variables for. Many of the static variables require the submission for sufficient
      context to be able to produce a value. Variables are static within that submission
      context, i.e. they don't change because of filling out the form.
    :param variables_registry: The static variables registry to use. If not provided,
      the default registry will be used.

    You should not rely on the order of returned variables, as they are registered in
    the order the Django apps are loaded - and this may change without notice.
    """
    return [
        registered_variable.get_static_variable(submission=submission)
        for registered_variable in variables_registry or static_variables_registry
    ]


class PluginInfo(TypedDict):
    plugin_identifier: str
    plugin_verbose_name: StrOrPromise
    plugin_variables: list[FormVariable]


def get_registration_plugins_variables() -> list[PluginInfo]:
    """Return the registration plugin variables from the enabled plugins.

    The initial values aren't populated.
    """

    return [
        {
            "plugin_identifier": plugin.identifier,
            "plugin_verbose_name": plugin.verbose_name,
            "plugin_variables": get_static_variables(variables_registry=registry),
        }
        for plugin in registration_plugins_registry.iter_enabled_plugins()
        if (registry := plugin.get_variables_registry()) is not None
    ]
