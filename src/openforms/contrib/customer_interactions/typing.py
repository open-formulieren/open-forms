from collections.abc import Sequence
from typing import TypedDict

from openforms.formio.typing.custom import SupportedChannels


# this defines the shape that it's saved in the variable when we fetch the addresses
class CommunicationChannelOptions(TypedDict):
    address: str
    verification_date: str | None


class CommunicationChannel(TypedDict):
    type: SupportedChannels
    options: Sequence[CommunicationChannelOptions]
    preferred: str | None  # The preferred address in this channel


# this defines the shape of the addresses that the frontend receives
class CommunicationChannelReturnOptions(TypedDict):
    address: str
    is_verified: bool


class CommunicationChannelReturn(TypedDict):
    type: SupportedChannels
    options: Sequence[CommunicationChannelReturnOptions]
    preferred: str | None  # The preferred address in this channel
