from __future__ import annotations

from django.utils.translation import get_language

from openproduct_client import OpenProductClient
from openproduct_client.structs.base import PaginationParams
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from .exceptions import NoServiceConfigured
from .models import ProductConfiguration


def get_open_product_client(service: Service | None = None) -> OpenProductClient:
    """
    Return the Open Product Client based on the service provided.

    The Open Product supports two different APIs ``/producten/api/v1`` and
    ``/producttypen/api/v1``. The type of the API is defined according to the resource
    type we access.
    """
    if not service:
        config = ProductConfiguration.get_solo()
        if not (service := config.open_product_service):
            raise NoServiceConfigured("No Open Product service defined, aborting.")

    return build_client(
        service,
        client_factory=OpenProductClient,
        language_code=get_language(),
    )


def check_open_product_config() -> str:
    """
    Health check function for the Open Product interaction.
    """
    try:
        with get_open_product_client() as client:
            params = PaginationParams(page=1)
            client.content_label.list(params=params)
    except NoServiceConfigured:
        return ""
    except Exception as exc:
        return str(exc)

    return ""
