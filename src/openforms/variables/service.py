"""
Public Python API to access (static) form variables.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING

from openforms.plugins.registry import BaseRegistry

from .base import BaseStaticVariable
from .registry import register_static_variable as static_variables_registry
from .utils import get_variables_for_context

if TYPE_CHECKING:
    from openforms.forms.models import FormVariable
    from openforms.submissions.models import Submission

__all__ = ["get_static_variables", "get_variables_for_context", "resolve_key"]


type VariablesRegistry = BaseRegistry[BaseStaticVariable]


def get_static_variables(
    *,
    submission: Submission | None = None,
    variables_registry: VariablesRegistry | None = None,
    is_confirmation_email: bool = False,
) -> list[FormVariable]:
    """
    Return the full collection of static variables registered by all apps.

    :param submission: Optional, but recommended - the submission instance to get the
      variables for. Many of the static variables require the submission for sufficient
      context to be able to produce a value. Variables are static within that submission
      context, i.e. they don't change because of filling out the form.
    :param variables_registry: The static variables registry to use. If not provided,
      the default registry will be used.
    :param is_confirmation_email: The boolean flag. If 'true' the result excludes variables
      with the property 'exclude_from_confirmation_email'. Default is False.

    You should not rely on the order of returned variables, as they are registered in
    the order the Django apps are loaded - and this may change without notice.
    """
    if variables_registry is None:
        variables_registry = static_variables_registry

    return [
        registered_variable.get_static_variable(submission=submission)
        for registered_variable in variables_registry
        if not (
            is_confirmation_email
            and registered_variable.exclude_from_confirmation_email
        )
    ]


def resolve_key(input_key: str, all_form_variable_keys: Collection[str]) -> str | None:
    """
    Resolve a (nested) key to its corresponding form variable key.

    Submission data of container-type components (e.g. editgrid, selectboxes, etc.)
    can be accessed with dot notation in a ``FormioData`` instance, but also in JSON
    logic. For example, key "selectboxes.a" with data ``{"a": "A", "b": "B"}``. This
    routine resolves the form variable key that corresponds to this data access key.

    :param input_key: The key to resolve.
    :param all_form_variable_keys: Collection of form variable keys to resolve for.
    :return: The resolved form variable key, or ``None`` if not resolved.
    """
    # There is a variable with this exact key, it is a valid reference.
    if input_key in all_form_variable_keys:
        return input_key

    # Process nested paths (editgrid, selectboxes, partners, children). Note that this
    # doesn't include other nested fields anymore, e.g. a textfield component with key
    # "foo.bar" will have already been resolved. We process all slices, as these keys
    # could also include dots.
    parts = input_key.split(".")
    for i in range(1, len(parts)):
        if (key := ".".join(parts[:i])) in all_form_variable_keys:
            return key

    # If none of the slices exist, we cannot resolve the complete key, so we just
    # return `None`. Note that the digest email should notify the user of invalid
    # logic rules.
    return None
