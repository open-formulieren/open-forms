from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from glom import Path, glom
from requests.exceptions import RequestException

from openforms.contrib.objects_api.clients import ObjectsClient

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


def validate_object_ownership(
    submission: Submission,
    client: ObjectsClient,
    object_attribute: list[str] | Path,
) -> None:
    """
    Function to check whether the user associated with a Submission is the owner
    of an Object in the Objects API, by comparing the authentication attribute.

    This validation should only be done if the Submission has an `initial_data_reference`
    """
    assert submission.initial_data_reference

    try:
        auth_info = submission.auth_info
    except ObjectDoesNotExist:
        raise PermissionDenied("Cannot pass data reference as anonymous user")

    object = None
    try:
        object = client.get_object(submission.initial_data_reference)
    except RequestException:
        logger.exception(
            "Something went wrong while trying to retrieve "
            "object for initial_data_reference"
        )

    if not object:
        # If the object cannot be found, we cannot consider the ownership check failed
        # because it is not verified that the user is not the owner
        logger.info(
            "Could not find object for initial_data_reference: %s",
            submission.initial_data_reference,
        )
        return

    if glom(object["record"]["data"], *object_attribute) != auth_info.value:
        raise PermissionDenied("User is not the owner of the referenced object")
