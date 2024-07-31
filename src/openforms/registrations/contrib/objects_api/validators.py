from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from openforms.contrib.zgw.clients.catalogi import Catalogus

from .client import get_catalogi_client
from .models import ObjectsAPIGroupConfig


def validate_catalogue_reference(
    config: ObjectsAPIGroupConfig,
) -> Catalogus | None:
    domain = config.catalogue_domain
    rsin = config.catalogue_rsin

    if not domain and not rsin:
        return
    assert domain and rsin, "Domain and RSIN need to both be provided"

    if config.catalogi_service is None:
        # should not be possible due to the field being required, but it *can* be
        # because of incomplete data migrations (the DB allows null)
        error = ValidationError(
            _("You must select or set up a catalogi service to use."),
            code="missing_catalogi_service",
        )
        raise ValidationError({"catalogi_service": error})

    with get_catalogi_client(config) as client:
        catalogus = client.find_catalogus(domain=domain, rsin=rsin)
        if catalogus is None:
            error = ValidationError(
                _(
                    "The specified catalogue does not exist. Maybe you made a typo in "
                    "the domain or RSIN?"
                ),
                code="invalid_catalogus",
            )
            raise ValidationError({"catalogus_domain": error})
        return catalogus


_IOT_URL_FIELDS = (
    "informatieobjecttype_submission_report",
    "informatieobjecttype_submission_csv",
    "informatieobjecttype_attachment",
)


def validate_document_type_references(
    config: ObjectsAPIGroupConfig,
    catalogus: Catalogus,
) -> None:
    errors = {}
    for field in _IOT_URL_FIELDS:
        url = getattr(config, field)
        if not url:
            continue
        if url not in catalogus["informatieobjecttypen"]:
            errors[field] = ValidationError(
                _("The document type URL is not in the specified catalogue."),
                code="invalid_in_catalogue",
            )
    if errors:
        raise ValidationError(errors)
