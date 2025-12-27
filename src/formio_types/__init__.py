from __future__ import annotations

from collections.abc import Sequence

from .bsn import BSN
from .checkbox import Checkbox
from .columns import Column as BaseColumn, Columns as BaseColumns
from .content import Content
from .currency import Currency
from .date import Date
from .editgrid import EditGrid as BaseEditGrid
from .email import Email
from .fieldset import Fieldset as BaseFieldSet
from .file import File
from .phone_number import PhoneNumber
from .postcode import Postcode
from .radio import Radio
from .select import Select
from .textfield import TextField

# ordered as they are displayed in the formio builder UI
__all__ = [
    "AnyComponent",
    # basic
    "TextField",
    "Email",
    "Date",
    # "DateTime",
    # "Time",
    "PhoneNumber",
    "File",
    # "Textarea",
    # "Number",
    # "Map",
    "Checkbox",
    # "Selectboxes",
    "Select",
    "Currency",
    "Radio",
    # special
    # "IBAN",
    # "LicensePlate",
    "Postcode",
    "BSN",
    # "Signature",
    # "Cosign",
    "EditGrid",
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


class EditGrid(BaseEditGrid):
    components: Sequence[AnyComponent]


# Discriminated union of all possible component types - ordered as they are displayed
# in the formio builder UI

type AnyComponent = (
    # basic
    TextField
    | Email
    | Date
    | PhoneNumber
    | File
    | Checkbox
    | Select
    | Currency
    | Radio
    # special
    | Postcode
    | BSN
    | EditGrid
    | Content
    | Columns
    | Fieldset
    # deprecated
)
