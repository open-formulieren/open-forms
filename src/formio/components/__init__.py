from __future__ import annotations

from .address_nl import AddressNL

# ordered as they are displayed in the formio builder UI
__all__ = [  # noqa: RUF022
    # Special fields
    "AddressNL",
]

# Discriminated union of all possible component types - ordered as they are displayed
# in the formio builder UI

type AnyComponent = (
    # Special fields
    AddressNL
)
