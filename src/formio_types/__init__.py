from __future__ import annotations

from collections.abc import MutableMapping, Sequence

import msgspec

from ._base import Component, Option
from .address_nl import AddressNL
from .bsn import BSN
from .checkbox import Checkbox
from .children import Children
from .columns import Column as BaseColumn, Columns as BaseColumns
from .content import Content
from .cosign import CosignV1, CosignV2
from .currency import Currency
from .customer_profile import CustomerProfile
from .date import Date
from .datetime import DateTime
from .editgrid import EditGrid as BaseEditGrid
from .email import Email
from .fieldset import Fieldset as BaseFieldSet
from .file import File
from .iban import Iban
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
__all__ = [
    "AnyComponent",
    "FormioConfiguration",
    "TYPE_TO_TAG",
    "Option",
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
    "NpFamilyMembers",
    "Signature",
    "CosignV2",
    "Map",
    "EditGrid",
    "AddressNL",
    "Partners",
    "Children",
    "CustomerProfile",
    # layout
    "Content",
    "Columns",
    "Fieldset",
    "SoftRequiredErrors",
    # deprecated
    "CosignV1",
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
    | NpFamilyMembers
    | Signature
    | CosignV2
    | Map
    | EditGrid
    | AddressNL
    | Partners
    | Children
    | CustomerProfile
    # layout
    | Content
    | Columns
    | Fieldset
    | SoftRequiredErrors
    # deprecated
    | CosignV1
)


class FormioConfiguration(msgspec.Struct, kw_only=True):
    components: Sequence[AnyComponent]


TYPE_TO_TAG: MutableMapping[type[Component], str] = {}


def _all_subclasses(cls: type[Component]):
    if not (subs := cls.__subclasses__()):
        yield cls
    for sub in subs:
        yield from _all_subclasses(sub)


# build the tag registry
for component_t in _all_subclasses(Component):
    cfg = component_t.__struct_config__
    assert isinstance(cfg.tag, str)
    TYPE_TO_TAG[component_t] = cfg.tag
