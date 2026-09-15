from collections.abc import Sequence
from typing import TypedDict

from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)
from openforms.formio.typing.custom import SupportedChannels


class CommunicationPreferencesOptions(TypedDict):
    customer_interactions_api_group: CustomerInteractionsAPIGroupConfig
    profile_form_variable: str


class EmailCommunicationChannelOptions(TypedDict):
    email_address: str
    verification_date: str | None


class PhoneCommunicationChannelOptions(TypedDict):
    phone_number_address: str
    verification_date: str | None


class CommunicationChannel(TypedDict):
    type: SupportedChannels
    options: Sequence[
        EmailCommunicationChannelOptions | PhoneCommunicationChannelOptions
    ]
    preferred: str | None  # The preferred address in this channel
