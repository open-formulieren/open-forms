from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict

from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)


class ProfileCommunicationPreferencesOptions(TypedDict):
    customer_interactions_api_group: CustomerInteractionsAPIGroupConfig
    profile_form_variable: str


class DigitalAddressResponse(TypedDict, total=False):
    emails: list[str]
    preferred_email: str | None
    phone_numbers: list[str]
    preferred_phone_number: str | None


class CommunicationChannelPreferences(TypedDict):
    options: Sequence[str]
    preferred: str | None


type SupportedChannels = Literal["email", "phone_number"]
type ProfileCommunicationChannels = Mapping[
    SupportedChannels, CommunicationChannelPreferences
]
