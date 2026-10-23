from __future__ import annotations

from django.utils.translation import get_language

import msgspec
from furl import furl
from openproduct_client.clients import OpenProductClient
from openproduct_client.structs.base import (
    PaginatedResponseBody,
    PaginationParams,
)
from openproduct_client.structs.product_type import (
    ContentLabel,
)
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.client import LoggingMixin

from .constants import (
    OPEN_PRODUCT_API_MAPPINGS,
    OpenProductApiOptions,
)
from .exceptions import NoServiceConfigured
from .models import ProductConfiguration


def get_open_product_client(
    api_type: OpenProductApiOptions, service: Service | None
) -> ProductTypeClient:
    """
    Return the Open Product Client based on the type.

    The Open Product supports two different APIs so we build the one that was asked to.
    The products are defined in ``/producten/api/v1`` and the product types in
    ``/producttypen/api/v1``.
    """
    if not service:
        raise NoServiceConfigured("No Open Product service defined, aborting.")

    assert isinstance(service, Service)

    base_url = furl(service.api_root.rstrip("/"))

    # make sure the service is updated properly according to the api type
    if not base_url.path == furl(OPEN_PRODUCT_API_MAPPINGS[api_type]).path:
        service.api_root = f"{base_url.origin}/{api_type}/api/v1"
        service.save()

    return build_client(
        service,
        client_factory=ProductTypeClient,
        language_code=get_language(),
    )


class ProductTypeClient(LoggingMixin, OpenProductClient):
    """
    The Client that supports the necessary methods regarding the product types.
    """

    def list_content_labels(
        self, params: PaginationParams | None = None
    ) -> PaginatedResponseBody[ContentLabel]:
        """
        Get all the available content labels (based on query parameters).
        """
        response = self.content_label.list(params=params)
        return response


def check_open_product_config() -> str:
    """
    Health check function for the Open Product interaction.
    """
    config = ProductConfiguration.get_solo()
    if not config.open_product_service:
        return ""

    with get_open_product_client(
        OpenProductApiOptions.product_type, config.open_product_service
    ) as client:
        # perform a cheap API call
        params = PaginationParams(page=1)

        try:
            client.content_label.list(params=msgspec.to_builtins(params))
        except Exception as exc:
            return exc.args[0]

        return ""
