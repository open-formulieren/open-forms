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

# ordered as they are displayed in the formio builder UI
__all__ = [  # noqa: RUF022
    # Form fields
    "Email",
    "Date",
    "DateTime",
    "PhoneNumber",
    "Postcode",
    "File",
    "Number",
    "Checkbox",
    "Currency",
    # Special fields
    "IBAN",
    "LicensePlate",
    "BSN",
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
]

# Discriminated union of all possible component types - ordered as they are displayed
# in the formio builder UI

# fmt: off
type AnyComponent = (
    # Form fields
    Email
    | Date
    | DateTime
    | PhoneNumber
    | Postcode
    | File
    | Number
    | Checkbox
    | Currency
    # Special fields
    | IBAN
    | LicensePlate
    | BSN
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
)
# fmt: on
