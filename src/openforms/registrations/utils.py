from collections.abc import Callable

from glom import assign, glom

from openforms.submissions.models import Submission

unset = object()


def execute_unless_result_exists[R](
    callback: Callable[[], R],
    submission: Submission,
    spec: str,
    default=None,
    result=unset,
) -> R:
    if submission.registration_result is None:
        submission.registration_result = {}

    existing_result = glom(submission.registration_result, spec, default=default)
    if existing_result:
        return existing_result

    callback_result = callback()

    if result is unset:
        result = callback_result

    # store the result
    assign(submission.registration_result, spec, result, missing=dict)
    submission.save(update_fields=["registration_result"])
    return callback_result
