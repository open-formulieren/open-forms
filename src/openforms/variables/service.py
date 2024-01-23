"""
Public Python API to access (static) form variables.
"""
from typing import Optional

from openforms.forms.models import FormVariable
from openforms.submissions.models import Submission

from .registry import register_static_variable as register

__all__ = ["get_static_variables"]


def get_static_variables(
    *, submission: Optional[Submission] = None
) -> list[FormVariable]:
    """
    Return the full collection of static variables registered by all apps.

    :param submission: Optional, but recommended - the submission instance to get the
      variables for. Many of the static variables require the submission for sufficient
      context to be able to produce a value. Variables are static within that submission
      context, i.e. they don't change because of filling out the form.

    You should not rely on the order of returned variables, as they are registered in
    the order the Django apps are loaded - and this may change without notice.
    """
    return [
        registered_variable.get_static_variable(submission=submission)
        for registered_variable in register
    ]
