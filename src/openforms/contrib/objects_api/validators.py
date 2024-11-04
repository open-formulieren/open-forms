from __future__ import annotations

import warnings
from functools import partial

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from openforms.contrib.zgw.clients.catalogi import Catalogus
from openforms.contrib.zgw.validators import (
    validate_catalogue_reference as _validate_catalogue_reference,
)

from .clients import get_catalogi_client
from .models import ObjectsAPIGroupConfig


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
