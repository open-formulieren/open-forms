from collections.abc import Sequence
from typing import TypedDict

from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)
from openforms.formio.typing.custom import SupportedChannels


class CommunicationPreferencesOptions(TypedDict):
    customer_interactions_api_group: CustomerInteractionsAPIGroupConfig
    profile_form_variable: str


class CommunicationChannel(TypedDict):
    type: SupportedChannels
    options: Sequence[str]
    preferred: str | None
