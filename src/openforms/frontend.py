from typing import Iterable, Literal, TypeAlias

from openforms.submissions.models import Submission

SDKAction: TypeAlias = Literal["stap", "afspraak-annuleren", "cosign"]


def get_frontend_redirect_url(
    submission: Submission,
    action: SDKAction,
    action_args: Iterable[str] | None = None,
    query: dict[str, str] | None = None,
) -> str:
    """Get the frontend redirect URL depending on the action.

    Some actions require arguments to be specified. The frontend will take care of building the right redirection
    based on the action and action arguments. Extra query parameters can be specified with ``query``.
    """
    f = submission.cleaned_form_url
    _query = {
        "_action": action,
    }
    if action_args:
        _query["_action_args"] = ",".join(action_args)
    if query:
        _query.update(query)

    return f.add(_query).url
