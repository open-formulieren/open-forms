import logging

from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission

from .exceptions import NoSubmissionReference

__all__ = ["NoSubmissionReference", "extract_submission_reference"]

logger = logging.getLogger(__name__)


def extract_submission_reference(submission: Submission) -> str:
    """
    Extract the (unique) and public submission reference from the submission result.

    :arg submission: :class:`Submission` instance to extract the reference for
    :raises NoSubmissionReference: if no reference could be extracted.
    """
    form = submission.form
    backend = form.registration_backend
    registry = form._meta.get_field("registration_backend").registry

    if not backend:
        raise NoSubmissionReference(
            "There is no backend configured for the form, nothing to extract."
        )

    if not submission.registration_status == RegistrationStatuses.success:
        raise NoSubmissionReference(
            "Submission registration did not succeed, there is no result data to process."
        )

    if not (result := submission.registration_result):
        raise NoSubmissionReference("No result data saved, nothing to extract.")

    # figure out which plugin to call for extraction
    plugin = registry[backend]

    try:
        return plugin.get_reference_from_result(result)
    except Exception as exc:
        raise NoSubmissionReference("Extraction failed") from exc
