from typing import NotRequired, TypedDict


# Source for the typed dict definitions:
# https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html
# Asked JCC: "string or null" means that the field can be missing entirely. Which is
# confirmed by looking at the example data in our VCR cassettes. None of fields have the
# value `null` - they are either filled or missing.
# Note that the documentation defines a "revision" key for most of these dicts, but
# NONE of the example data from their test environment include this, so decided to leave
# it out
class Version(TypedDict):
    warpApiVersion: NotRequired[str]
    afsprakenVersion: NotRequired[str]


class Activity(TypedDict):
    id: str
    number: int  # will be removed completely in the future, use "id" instead
    code: NotRequired[str]  # this is not used anymore actually
    description: NotRequired[str]
    necessities: NotRequired[str]
    appointmentDuration: int
    maxCountForEvent: NotRequired[int]
    activityGroupId: NotRequired[str]
    synonyms: NotRequired[list[str]]


class PhoneNumber(TypedDict):
    auditId: str
    id: str
    value: NotRequired[str]


class PhoneNumberType(TypedDict):
    auditId: str
    id: str
    name: NotRequired[str]
    description: NotRequired[str]


class LocationPhoneNumber(TypedDict):
    auditId: str
    id: str
    phoneNumber: PhoneNumber
    phoneNumberType: PhoneNumberType


class Country(TypedDict):
    id: str
    isoCode: NotRequired[str]
    name: NotRequired[str]


class Address(TypedDict):
    auditId: str
    id: str
    department: NotRequired[str]
    streetName: NotRequired[str]
    houseNumber: NotRequired[str]
    houseNumberSuffix: NotRequired[str]
    city: NotRequired[str]
    postalCode: NotRequired[str]
    province: NotRequired[str]
    country: Country
    customCountryIso: NotRequired[str]


class Location(TypedDict):
    auditId: str
    id: str
    isActive: NotRequired[bool]
    code: NotRequired[str]
    phoneNumberList: NotRequired[list[LocationPhoneNumber]]
    description: NotRequired[str]
    address: Address
    # not listed as optional in the documentation, but none of the example locations
    # include it
    synergyId: NotRequired[str]
    emailAddress: NotRequired[str]
    isDefault: bool
    smtpFromEmailAddress: NotRequired[str]
    smtpFromName: NotRequired[str]
    internetAppointmentBaseUrl: NotRequired[str]
    locationNumber: int  # will be removed completely in the future, use "id" instead
