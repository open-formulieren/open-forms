from __future__ import annotations

import logging
import warnings
from functools import partial
from typing import TYPE_CHECKING

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

from glom import glom
from requests.exceptions import RequestException

from openforms.contrib.objects_api.clients import (
    NoServiceConfigured,
    get_objects_client,
)
from openforms.contrib.zgw.clients.catalogi import Catalogus
from openforms.contrib.zgw.validators import (
    validate_catalogue_reference as _validate_catalogue_reference,
)

from .clients import get_catalogi_client
from .models import ObjectsAPIGroupConfig

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


def validate_catalogue_reference(
    config: ObjectsAPIGroupConfig,
) -> Catalogus | None:
    return _validate_catalogue_reference(
        domain=config.catalogue_domain,
        rsin=config.catalogue_rsin,
        catalogi_service=config.catalogi_service,
        get_client=partial(get_catalogi_client, config),
    )


_IOT_URL_FIELDS = (
    "informatieobjecttype_submission_report",
    "informatieobjecttype_submission_csv",
    "informatieobjecttype_attachment",
)

_IOT_DESCRIPTION_FIELDS = (
    "iot_submission_report",
    "iot_submission_csv",
    "iot_attachment",
)


def validate_document_type_references(
    config: ObjectsAPIGroupConfig,
    catalogus: Catalogus,
) -> None:
    errors = {}

    # Legacy behaviour - validate the explicit URL references
    for field in _IOT_URL_FIELDS:
        url = getattr(config, field)
        if not url:
            continue
        warnings.warn(
            "URL references to document types are deprecated and will be remove in "
            "Open Forms 3.0",
            DeprecationWarning,
        )
        if url not in catalogus["informatieobjecttypen"]:
            errors[field] = ValidationError(
                _("The document type URL is not in the specified catalogue."),
                code="invalid_in_catalogue",
            )

    with get_catalogi_client(config) as client:
        for field in _IOT_DESCRIPTION_FIELDS:
            if not (description := getattr(config, field)):
                continue
            versions = client.find_informatieobjecttypen(
                catalogus=catalogus["url"], description=description
            )
            if versions is None:
                errors[field] = ValidationError(
                    _("No document type with description {description} found.").format(
                        description=description
                    ),
                    code="not-found",
                )

    if errors:
        raise ValidationError(errors)


def validate_object_ownership(submission: Submission) -> None:
    form = submission.form

    try:
        auth_info = submission.auth_info
    except ObjectDoesNotExist:
        raise PermissionDenied("Cannot pass data reference as anonymous user")

    object = None
    for backend in form.registration_backends.filter(backend="objects_api"):
        if not backend.options:
            continue

        api_group = ObjectsAPIGroupConfig.objects.filter(
            pk=backend.options.get("objects_api_group")
        ).first()
        if not api_group:
            continue

        try:
            with get_objects_client(api_group) as client:
                try:
                    object = client.get_object(submission.initial_data_reference)
                    break
                except RequestException:
                    logger.exception(
                        "Something went wrong while trying to retrieve "
                        "object for initial_data_reference"
                    )
        except NoServiceConfigured:
            logger.exception(
                "Something went wrong while trying to create a client "
                "for Objects API"
            )

    if not object:
        # If the object cannot be found, we cannot consider the ownership check failed
        # because it is not verified that the user is not the owner
        logger.info(
            "Could not find object for initial_data_reference: %s",
            submission.initial_data_reference,
        )
        return

    # TODO should this path be configurable?
    if glom(object["record"]["data"], auth_info.attribute) != auth_info.value:
        raise PermissionDenied("User is not the owner of the referenced object")
