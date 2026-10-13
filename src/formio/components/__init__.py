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
from .email import Email
from .file import File
from .iban import IBAN
from .licenseplate import LicensePlate
from .map import Map
from .np_family_members import NpFamilyMembers
from .number import Number
from .partners import Partners
from .phone_number import PhoneNumber
from .postcode import Postcode
from .radio import Radio
from .select import Select
from .selectboxes import Selectboxes
from .signature import Signature
from .soft_required_errors import SoftRequiredErrors
from .textarea import Textarea
from .textfield import TextField
from .time import Time

# ordered as they are displayed in the formio builder UI
__all__ = [  # noqa: RUF022
    # Form fields
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
    # Special fields
    "IBAN",
    "LicensePlate",
    "BSN",
    "Signature",
    "CosignV2",
    "Map",
    "AddressNL",
    "Partners",
    "Children",
    "CustomerProfile",
    "NpFamilyMembers",
    "CosignV1",
    # Layout
    "Content",
    "SoftRequiredErrors",
]

# Discriminated union of all possible component types - ordered as they are displayed
# in the formio builder UI

type AnyComponent = (
    # Form fields
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
    # Special fields
    | IBAN
    | LicensePlate
    | BSN
    | Signature
    | CosignV2
    | Map
    | AddressNL
    | Partners
    | Children
    | CustomerProfile
    | NpFamilyMembers
    | CosignV1
    # Layout
    | Content
    | SoftRequiredErrors
)
