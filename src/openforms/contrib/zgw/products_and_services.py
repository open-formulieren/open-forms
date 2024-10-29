"""
Support resolving products and services referenced by case types.

.. warning:: Products and services integration is experimental. There is no standard for it yet.
"""

from typing import TypedDict

from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.zgw.clients.catalogi import CaseType


class Product(TypedDict):
    # This configuration is based on sample test data. This will have to be revisited when there is a real API spec.
    # The sample data shows more attributes, but we currently don't use them.
    url: str
    description: str


def resolve_case_type_products(case_type_versions: list[CaseType]) -> list[Product]:
    all_urls: set[str] = set(
        sum((version["productenOfDiensten"] for version in case_type_versions), [])
    )
    products: list[Product] = []

    for url in all_urls:
        description = ""

        # Fetch product content
        service = Service.get_service(url)
        if service:
            client = build_client(service)
            response = client.get(url)
            if response.ok:
                description = response.json().get("description")

        products.append(Product(url=url, description=description))

    return products
