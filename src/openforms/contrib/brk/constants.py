from typing import NotRequired, TypedDict


class AddressValue(TypedDict):
    postcode: str
    house_number: str
    house_letter: NotRequired[str]
    house_number_addition: NotRequired[str]
    city: NotRequired[str]
    streetName: NotRequired[str]
    secretStreetCity: NotRequired[str]
