from typing import TypedDict


class KlantInteractiesOptions(TypedDict):
    email: bool
    phone_number: bool


class DigitalAddressResponse(TypedDict, total=False):
    emails: list[str]
    preferred_email: str | None
    phone_numbers: list[str]
    preferred_phone_number: str | None
