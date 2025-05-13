from typing import TypedDict

from .constants import FamilyMembersTypeChoices


class FamilyMembersPartnerOptions(TypedDict):
    mutable_data_form_variable: str
    type: FamilyMembersTypeChoices


class FamilyMembersChildOptions(TypedDict):
    mutable_data_form_variable: str
    type: FamilyMembersTypeChoices
    min_age: int | None
    max_age: int | None
    include_deceased: bool
