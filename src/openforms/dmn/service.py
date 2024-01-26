"""
Public Python API for the DMN module.
"""

from typing import Any

from .base import BasePlugin
from .registry import register

__all__ = ["evaluate_dmn", "VariablesMapping"]

VariablesMapping = dict[str, Any]


def evaluate_dmn(
    plugin_id: str,
    definition_id: str,
    *,
    version: str = "",
    input_values: VariablesMapping
) -> VariablesMapping:
    """
    Evaluate the decision definition using the spefified plugin.

    :arg plugin_id: identifier of the plugin to use for evaluation
    :arg definition_id: identifier of the decision definition to evaluate
    :arg version: optional version of the definition to evaluate, if supported. If
      versioning is supported but no version is specified, the latest version should be
      used.
    :arg input_values: A mapping of variable name -> variable value, used as input
      variables for the evaluation.
    :returns: A mapping of name -> value output variables.
    """
    plugin: BasePlugin = register[plugin_id]
    return plugin.evaluate(definition_id, version=version, input_values=input_values)
