import logging
from typing import Optional

from openforms.submissions.models import Submission

logger = logging.getLogger(__name__)


def register_submission(submission: Submission) -> Optional[dict]:
    # figure out which registry and backend to use from the model field used
    form = submission.form
    backend = form.registration_backend
    registry = form._meta.get_field("registration_backend").registry

    if not backend:
        logger.info("Form %s has no registration plugin configured, aborting")
        return

    plugin = registry[backend]

    import bpdb

    bpdb.set_trace()

    backend_func = registry.get(submission.form.backend)
    if backend_func:
        result = backend_func(submission)
        submission.backend_result = result
