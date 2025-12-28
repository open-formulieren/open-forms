from __future__ import annotations

from collections.abc import Sequence

from .bsn import BSN
from .checkbox import Checkbox
from .columns import Column as BaseColumn, Columns as BaseColumns
from .content import Content
from .cosign import CosignV2
from .currency import Currency
from .date import Date
from .datetime import DateTime
from .editgrid import EditGrid as BaseEditGrid
from .email import Email
from .fieldset import Fieldset as BaseFieldSet
from .file import File
from .iban import Iban
from .licenseplate import LicensePlate
from .map import Map
from .number import Number
from .phone_number import PhoneNumber
from .postcode import Postcode
from .radio import Radio
from .select import Select
from .selectboxes import Selectboxes
from .soft_required_errors import SoftRequiredErrors
from .textarea import Textarea
from .textfield import TextField
from .time import Time

# ordered as they are displayed in the formio builder UI
__all__ = [
    "AnyComponent",
    # basic
    "TextField",
    "Email",
    "Date",
    "DateTime",
    "Time",
    "PhoneNumber",
    "Postcode",
    "File",
    "Textarea",
    "Number",
    "Checkbox",
    "Selectboxes",
    "Select",
    "Currency",
    "Radio",
    # special
    "Iban",
    "LicensePlate",
    "BSN",
    # "npFamilyMembers",
    # "Signature",
    "CosignV2",
    "Map",
    "EditGrid",
    # "AddressNL",
    # "Partners",
    # "Children",
    # "CustomerProfile",
    # layout
    "Content",
    "Columns",
    "Fieldset",
    "SoftRequiredErrors",
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
    | DateTime
    | Time
    | PhoneNumber
    | Postcode
    | File
    | Textarea
    | Number
    | Checkbox
    | Selectboxes
    | Select
    | Currency
    | Radio
    # special
    | Iban
    | LicensePlate
    | BSN
    | CosignV2
    | Map
    | EditGrid
    # layout
    | Content
    | Columns
    | Fieldset
    | SoftRequiredErrors
    # deprecated
)
