"""
Public Python API to access (static) form variables.
"""

from openforms.forms.models import FormVariable
from openforms.plugins.registry import BaseRegistry
from openforms.submissions.models import Submission

from .base import BaseStaticVariable
from .registry import register_static_variable as static_variables_registry
from .utils import get_variables_for_context

__all__ = ["get_static_variables", "get_variables_for_context"]


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
