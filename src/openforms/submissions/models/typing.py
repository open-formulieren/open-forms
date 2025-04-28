from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from openforms.authentication.service import AuthAttribute


class SubmissionCosignData(TypedDict):
    # Rougly follows FormAuth, but converts to python data types
    plugin: str
    attribute: AuthAttribute
    value: str
    cosign_date: datetime
