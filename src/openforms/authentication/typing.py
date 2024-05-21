from typing import TypedDict

from .constants import AuthAttribute


class BaseAuth(TypedDict):
    """The base structure of authentication data."""

    plugin: str
    """The unique identifier of the plugin that inititiated the authentication data."""

    attribute: AuthAttribute
    value: str
