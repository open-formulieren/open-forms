from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

from django.conf import settings

from openforms.registrations.contrib.objects_api.utils import (
    recursively_escape_html_strings,
)
from openforms.typing import JSONObject, VariableValue
from openforms.utils.date import parse_date

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


def check_date(value: str) -> str:
    # raises ValueError if it's not a date or datetime
    parse_date(value)
    return value


def check_time(value: str) -> str:
    try:
        time.fromisoformat(value)
    except ValueError:
        datetime.fromisoformat(value)
    return value


def check_initial_value(initial_value: JSONObject, data_type: str) -> JSONObject:
    from .constants import CHECK_VARIABLE_TYPE, DEFAULT_INITIAL_VALUE

    try:
        return CHECK_VARIABLE_TYPE[data_type](initial_value)
    except (ValueError, TypeError):
        return DEFAULT_INITIAL_VALUE[data_type]


def get_variables_for_context(submission: Submission) -> dict[str, VariableValue]:
    """
    Return the key/value pairs of data in the state (static, user-defined, and component
    variables). If specified in the settings, strings will be escaped for HTML.

    Note that depending on when it is called, the 'auth' static variables (auth_bsn,
    auth_kvk...) can be already hashed.
    """
    state = submission.load_submission_value_variables_state()
    data = state.get_data(include_static_variables=True).data

    if settings.ESCAPE_REGISTRATION_OUTPUT:
        data = recursively_escape_html_strings(data)

    return data
