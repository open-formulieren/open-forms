from typing import Required, TypedDict

from zgw_consumers.models import Service


class JSONRegistrationOptions(TypedDict):
    service : Required[Service]
    relative_api_endpoint : str
    form_variables: Required[list[str]]
