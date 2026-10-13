from __future__ import annotations

from .address_nl import AddressNL
from .bsn import BSN
from .checkbox import Checkbox

# ordered as they are displayed in the formio builder UI
__all__ = [  # noqa: RUF022
    # Form fields
    "Checkbox",
    # Special fields
    "BSN",
    "AddressNL",
]

# Discriminated union of all possible component types - ordered as they are displayed
# in the formio builder UI

# fmt: off
type AnyComponent = (
    Checkbox
    # Special fields
    | BSN
    | AddressNL
)
# fmt: on
