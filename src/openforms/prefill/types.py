from typing import Literal

from .constants import IdentifierRoles

IdentifierRole = (
    Literal[IdentifierRoles.main] | Literal[IdentifierRoles.authorised_person]
)
