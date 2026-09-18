from typing import TypedDict

from openforms.contrib.customer_interactions.models import (
    CustomerInteractionsAPIGroupConfig,
)


class CommunicationPreferencesOptions(TypedDict):
    customer_interactions_api_group: CustomerInteractionsAPIGroupConfig
    profile_form_variable: str
