from typing import TypedDict

from typing_extensions import NotRequired


class AddressValue(TypedDict):
    postcode: str
    house_number: str
    house_letter: NotRequired[str]
    house_number_addition: NotRequired[str]
