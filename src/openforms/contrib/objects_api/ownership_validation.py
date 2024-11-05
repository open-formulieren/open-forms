from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from glom import Path, glom
from requests.exceptions import RequestException

from openforms.contrib.objects_api.clients import ObjectsClient
from openforms.logging import logevent

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from openforms.prefill.contrib.objects_api.plugin import ObjectsAPIPrefill
    from openforms.registrations.contrib.objects_api.plugin import (
        ObjectsAPIRegistration,
    )
    from openforms.submissions.models import Submission


def validate_object_ownership(
    submission: Submission,
    client: ObjectsClient,
    object_attribute: list[str],
    plugin: ObjectsAPIPrefill | ObjectsAPIRegistration,
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
        logger.exception(
            "Cannot perform object ownership validation for reference %s with unauthenticated user",
            submission.initial_data_reference,
        )
        logevent.object_ownership_check_anonymous_user(submission, plugin=plugin)
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

    if (
        glom(object["record"]["data"], Path(*object_attribute), default=None)
        != auth_info.value
    ):
        logger.exception(
            "Submission with initial_data_reference did not pass ownership check for reference %s",
            submission.initial_data_reference,
        )
        logevent.object_ownership_check_failure(submission, plugin=plugin)
        raise PermissionDenied("User is not the owner of the referenced object")

    logevent.object_ownership_check_success(submission, plugin=plugin)
