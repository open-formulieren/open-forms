from typing import Literal, TypedDict

from .constants import FamilyMembersTypeChoices


class PartnerOptions(TypedDict):
    type: Literal[FamilyMembersTypeChoices.partners]
    mutable_data_form_variable: str


class ChildOptions(TypedDict):
    type: Literal[FamilyMembersTypeChoices.children]
    mutable_data_form_variable: str
    min_age: int | None
    max_age: int | None
    include_deceased: bool


type FamilyMemberOptions = PartnerOptions | ChildOptions
