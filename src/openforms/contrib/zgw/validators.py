from collections.abc import Callable

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from zgw_consumers.models import Service

from .clients.catalogi import CatalogiClient, Catalogus


def validate_catalogue_reference(
    *,
    domain: str,
    rsin: str,
    catalogi_service: Service | None,
    get_client: Callable[[], CatalogiClient],
    catalogi_field: str = "catalogi_service",
) -> Catalogus | None:
    if not domain and not rsin:
        return
    assert domain and rsin, "Domain and RSIN need to both be provided"

    if catalogi_service is None:
        # should not be possible due to the field being required, but it *can* be
        # because of incomplete data migrations (the DB allows null)
        error = ValidationError(
            _("You must select or set up a catalogi service to use."),
            code="missing_catalogi_service",
        )
        raise ValidationError({catalogi_field: error})

    with get_client() as client:
        catalogus = client.find_catalogus(domain=domain, rsin=rsin)
        if catalogus is None:
            error = ValidationError(
                _(
                    "The specified catalogue does not exist. Maybe you made a typo in "
                    "the domain or RSIN?"
                ),
                code="invalid-catalogue",
            )
            raise ValidationError({"catalogue_domain": error})
        return catalogus
