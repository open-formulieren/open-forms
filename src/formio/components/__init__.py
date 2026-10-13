from __future__ import annotations

from .address_nl import AddressNL
from .bsn import BSN
from .checkbox import Checkbox
from .children import Children
from .content import Content
from .cosign import CosignV1, CosignV2
from .currency import Currency
from .customer_profile import CustomerProfile
from .date import Date
from .datetime import DateTime

# ordered as they are displayed in the formio builder UI
__all__ = [  # noqa: RUF022
    # Form fields
    "Date",
    "DateTime",
    "Checkbox",
    "Currency",
    # Special fields
    "BSN",
    "CosignV2",
    "AddressNL",
    "Children",
    "CustomerProfile",
    "CosignV1",
    # Layout
    "Content",
]

# Discriminated union of all possible component types - ordered as they are displayed
# in the formio builder UI

# fmt: off
type AnyComponent = (
    # Form fields
    Date
    | DateTime
    | Checkbox
    | Currency
    # Special fields
    | BSN
    | CosignV2
    | AddressNL
    | Children
    | CustomerProfile
    | CosignV1
    # Layout
    | Content
)
# fmt: on
