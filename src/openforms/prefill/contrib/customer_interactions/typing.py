from collections.abc import Sequence
from typing import Literal, TypedDict

from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)


class CommunicationPreferencesOptions(TypedDict):
    customer_interactions_api_group: CustomerInteractionsAPIGroupConfig
    profile_form_variable: str


type SupportedChannels = Literal["email", "phoneNumber"]


class CommunicationChannel(TypedDict):
    type: SupportedChannels
    options: Sequence[str]
    preferred: str | None
