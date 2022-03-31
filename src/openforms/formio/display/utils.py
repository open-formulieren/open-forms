from typing import Any, Dict, Iterable, Tuple

from openforms.submissions.form_logic import evaluate_form_logic
from openforms.submissions.models import Submission, SubmissionStep


def iter_processed_steps(
    submission: Submission,
) -> Iterable[Tuple[SubmissionStep, Dict[str, Any]]]:
    # TODO get rid of context, see ticket #1068
    # not this will break on prefills.. ayayay
    context = {}

    for step in submission.steps:
        configuration = evaluate_form_logic(
            submission,
            step,
            submission.data,
            context,
        )
        yield step, configuration
