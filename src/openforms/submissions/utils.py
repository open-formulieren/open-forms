from typing import Union

from django.http import HttpRequest

from rest_framework.request import Request

from .constants import SUBMISSIONS_SESSION_KEY
from .models import Submission


def add_submmission_to_session(
    submission: Submission, request: Union[Request, HttpRequest]
) -> None:
    """
    Store the submission UUID in the request session for authorization checks.
    """
    # note: possible race condition with concurrent requests
    submissions = request.session.get(SUBMISSIONS_SESSION_KEY, [])
    submissions.append(str(submission.uuid))
    request.session[SUBMISSIONS_SESSION_KEY] = submissions


def remove_submission_from_session(
    submission: Submission, request: Union[Request, HttpRequest]
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    id_to_check = str(submission.uuid)
    submissions = request.session.get(SUBMISSIONS_SESSION_KEY, [])
    if id_to_check in submissions:
        submissions.remove(id_to_check)
        request.session[SUBMISSIONS_SESSION_KEY] = submissions
