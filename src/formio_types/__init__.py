from __future__ import annotations

from collections.abc import Sequence

from .bsn import BSN
from .checkbox import Checkbox
from .columns import Column as BaseColumn, Columns as BaseColumns
from .content import Content
from .date import Date
from .fieldset import Fieldset as BaseFieldSet
from .phone_number import PhoneNumber
from .postcode import Postcode
from .textfield import TextField

# ordered as they are displayed in the formio builder UI
__all__ = [
    "AnyComponent",
    # basic
    "TextField",
    # "Email",
    "Date",
    # "DateTime",
    # "Time",
    "PhoneNumber",
    # "File",
    # "Textarea",
    # "Number",
    # "Map",
    "Checkbox",
    # "Selectboxes",
    # "Select",
    # "Currency",
    # "Radio",
    # special
    # "IBAN",
    # "LicensePlate",
    "Postcode",
    "BSN",
    # "Signature",
    # "Cosign",
    # "EditGrid",
    # "AddressNL",
    # "Partners",
    # "Children",
    # "CustomerProfile",
    # layout
    "Content",
    "Columns",
    "Fieldset",
    # "SoftRequiredErrors",
    # deprecated
    # "CosignOld",
]

# Component types - these cannot be split into the layout modules due to circular
# import challenges :(


class Fieldset(BaseFieldSet):
    components: Sequence[AnyComponent]


class Column(BaseColumn):
    components: Sequence[AnyComponent]


class Columns(BaseColumns):
    columns: Sequence[Column]


# Discriminated union of all possible component types - ordered as they are displayed
# in the formio builder UI

type AnyComponent = (
    TextField
    | Date
    | PhoneNumber
    | Checkbox
    | Postcode
    | BSN
    | Content
    | Columns
    | Fieldset
)
