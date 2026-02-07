from __future__ import annotations

from django.core.exceptions import PermissionDenied

import structlog
from glom import Path, PathAccessError, glom
from requests.exceptions import RequestException

from openforms.contrib.objects_api.clients import ObjectsClient
from openforms.logging import audit_logger
from openforms.submissions.models import Submission

logger = structlog.stdlib.get_logger(__name__)


def validate_object_ownership(
    submission: Submission,
    client: ObjectsClient,
    object_attribute: list[str],
) -> None:
    """
    Function to check whether the user associated with a Submission is the owner
    of an Object in the Objects API, by comparing the authentication attribute.

    This validation should only be done if the Submission has an `initial_data_reference`
    """
    assert submission.initial_data_reference

    log = logger.bind(
        submission_uuid=str(submission.uuid),
        object_reference=submission.initial_data_reference,
        object_attribute=object_attribute,
    )
    audit_log = audit_logger.bind(**structlog.get_context(log))

    if not submission.is_authenticated:
        audit_log.warning(
            "object_ownership_failure", reason="submission_not_authenticated"
        )
        raise PermissionDenied("Cannot pass data reference as anonymous user")

    auth_info = submission.auth_info

    object = None
    try:
        object = client.get_object(submission.initial_data_reference)
    except RequestException as exc:
        log.error("objects_api_request_failure", exc_info=exc)
        raise PermissionDenied from exc

    if not object_attribute:
        log.error("object_ownership_failure", reason="no_auth_value_path_configured")
        raise PermissionDenied(
            "Could not verify if user is owner of the referenced object"
        )

    try:
        auth_value = glom(object["record"]["data"], Path(*object_attribute))
    except PathAccessError as exc:
        audit_log.error(
            "object_ownership_failure", reason="invalid_path_lookup", exc_info=exc
        )
        raise PermissionDenied(
            "Could not verify if user is owner of the referenced object"
        ) from exc

    if auth_value != auth_info.value:
        audit_log.error("object_ownership_failure", reason="different_owner")
        raise PermissionDenied("User is not the owner of the referenced object")

    audit_log.info("object_ownership_passed")
