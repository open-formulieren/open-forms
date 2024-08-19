from __future__ import annotations

from functools import partial

from openforms.contrib.zgw.clients.catalogi import Catalogus
from openforms.contrib.zgw.validators import (
    validate_catalogue_reference as _validate_catalogue_reference,
)

from .client import get_catalogi_client
from .models import ZGWApiGroupConfig


def validate_catalogue_reference(config: ZGWApiGroupConfig) -> Catalogus | None:
    return _validate_catalogue_reference(
        domain=config.catalogue_domain,
        rsin=config.catalogue_rsin,
        catalogi_service=config.ztc_service,
        get_client=partial(get_catalogi_client, config),
        catalogi_field="ztc_service",
    )
