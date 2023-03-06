from datetime import datetime, time

from openforms.typing import JSONObject
from openforms.utils.date import parse_date


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


def get_variables_for_context(submission) -> dict[str, JSONObject]:
    """Return the key/value pairs of static variables and submission variables.

    This returns the saved component variables and user defined variables for a submission, plus the static variables
    (which are never saved). Note that depending on when it is called, the 'auth' static variables
    (auth_bsn, auth_kvk...) can be already hashed.
    """
    from .service import get_static_variables

    return {
        **{
            variable.key: variable.initial_value
            for variable in get_static_variables(submission=submission)
        },
        **submission.data,
    }
