from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied

from glom import Path, PathAccessError, glom
from requests.exceptions import RequestException

from openforms.contrib.objects_api.clients import ObjectsClient
from openforms.logging import logevent
from openforms.prefill.base import BasePlugin as BasePrefillPlugin
from openforms.registrations.base import BasePlugin as BaseRegistrationPlugin
from openforms.submissions.models import Submission

logger = logging.getLogger(__name__)


def validate_object_ownership(
    submission: Submission,
    client: ObjectsClient,
    object_attribute: list[str],
    plugin: BasePrefillPlugin | BaseRegistrationPlugin,
) -> None:
    """
    Function to check whether the user associated with a Submission is the owner
    of an Object in the Objects API, by comparing the authentication attribute.

    This validation should only be done if the Submission has an `initial_data_reference`
    """
    assert submission.initial_data_reference

    if not submission.is_authenticated:
        logger.warning(
            "Cannot perform object ownership validation for reference %s with unauthenticated user",
            submission.initial_data_reference,
        )
        logevent.object_ownership_check_anonymous_user(submission, plugin=plugin)
        raise PermissionDenied("Cannot pass data reference as anonymous user")

    auth_info = submission.auth_info

    object = None
    try:
        object = client.get_object(submission.initial_data_reference)
    except RequestException as e:
        logger.exception(
            "Something went wrong while trying to retrieve "
            "object for initial_data_reference"
        )
        raise PermissionDenied from e

    if not object_attribute:
        logger.exception(
            "No path for auth value configured: %s, cannot perform ownership check",
            object_attribute,
        )
        raise PermissionDenied(
            "Could not verify if user is owner of the referenced object"
        )

    try:
        auth_value = glom(object["record"]["data"], Path(*object_attribute))
    except PathAccessError as e:
        logger.exception(
            "Could not retrieve auth value for path %s, it could be incorrectly configured",
            object_attribute,
        )
        raise PermissionDenied(
            "Could not verify if user is owner of the referenced object"
        ) from e

    if auth_value != auth_info.value:
        logger.warning(
            "Submission with initial_data_reference did not pass ownership check for reference %s",
            submission.initial_data_reference,
        )
        logevent.object_ownership_check_failure(submission, plugin=plugin)
        raise PermissionDenied("User is not the owner of the referenced object")

    logevent.object_ownership_check_success(submission, plugin=plugin)
