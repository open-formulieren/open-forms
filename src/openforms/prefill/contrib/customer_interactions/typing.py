from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict

from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)


class CommunicationPreferencesOptions(TypedDict):
    customer_interactions_api_group: CustomerInteractionsAPIGroupConfig
    profile_form_variable: str


class CommunicationChannelPreferences(TypedDict):
    options: Sequence[str]
    preferred: str | None


type SupportedChannels = Literal["email", "phone_number"]
type ProfileCommunicationChannels = Mapping[
    SupportedChannels, CommunicationChannelPreferences
]
