from collections.abc import Sequence
from typing import TypedDict


class ProductDetails(TypedDict):
    product_name: str
    product_content: Sequence[str]
