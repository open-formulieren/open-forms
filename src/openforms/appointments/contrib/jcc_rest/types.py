from typing import Literal, NotRequired, TypedDict

from openforms.typing import JSONPrimitive

# Source for the typed dict definitions:
# https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html
# Asked JCC: "string or null" means that the field can be missing entirely. Which is
# confirmed by looking at the example data in our VCR cassettes. None of fields have the
# value `null` - they are either filled or missing.
# Note that the documentation defines a "revision" key for most of these dicts, but
# NONE of the example data from their test environment include this, so decided to leave
# it out


# Fields with state Literal[0, 1, 2]
# 0: visible (it can be submitted without a value)
# 1: hidden (it's not shown and it's not required)
# 2: required (should be shown and should have a value)
FIELD_STATE = Literal[0, 1, 2]

# Fields with gender type Literal[0, 1, 2]
# 0: Other
# 1: male
# 2: female
GENDER_TYPE = Literal[0, 1, 2]


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


class BaseLocation(TypedDict):
    id: str
    description: NotRequired[str]


class Location(BaseLocation):
    auditId: str
    isActive: NotRequired[bool]
    code: NotRequired[str]
    phoneNumberList: NotRequired[list[LocationPhoneNumber]]
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


class CustomerFields(TypedDict):
    auditId: str
    id: NotRequired[str]
    gender: GENDER_TYPE
    firstName: FIELD_STATE
    initials: FIELD_STATE
    areFirstNameOrInitialsRequired: bool
    lastNamePrefix: FIELD_STATE
    birthDate: FIELD_STATE
    socialSecurityNumber: FIELD_STATE
    nationality: FIELD_STATE
    language: FIELD_STATE
    emailAddress: FIELD_STATE
    mainPhoneNumber: FIELD_STATE
    mobilePhoneNumber: FIELD_STATE
    isAnyPhoneNumberRequired: bool
    streetName: FIELD_STATE
    houseNumber: FIELD_STATE
    houseNumberSuffix: FIELD_STATE
    postalCode: FIELD_STATE
    city: FIELD_STATE
    country: FIELD_STATE
    isDefault: bool


class BaseAppointment(TypedDict):
    id: str
    code: int
    message: NotRequired[str]
    validateErrors: NotRequired[list[str]]
    acknowledgeIsSuccess: bool
    exception: NotRequired[str]
    logLevel: Literal[0, 1, 2, 3, 4]


class CreatedAppointment(BaseAppointment):
    pass


class CancelledAppointment(BaseAppointment):
    pass


class Customer(TypedDict):
    id: NotRequired[str]
    isMainCustomer: bool
    gender: GENDER_TYPE
    firstName: NotRequired[str]
    initials: NotRequired[str]
    lastNamePrefix: NotRequired[str]
    lastName: NotRequired[str]
    birthDate: NotRequired[str]  # ISO 8601 format
    emailAddress: NotRequired[str]
    phoneNumber: NotRequired[str]
    mobilePhoneNumber: NotRequired[str]
    streetName: NotRequired[str]
    houseNumber: NotRequired[int]
    houseNumberSuffix: NotRequired[str]
    postalCode: NotRequired[str]
    city: NotRequired[str]
    socialSecurityNumber: NotRequired[str]
    ssnCountryId: NotRequired[str]
    nationalityId: NotRequired[str]
    customNationality: NotRequired[str]
    languageId: NotRequired[str]
    addressCountryId: NotRequired[str]
    customCountryIso: NotRequired[str]


class Field(TypedDict):
    id: str
    fileName: NotRequired[str]
    file: NotRequired[str]
    value: NotRequired[str]
    fieldDefinitionId: str


class Payment(TypedDict):
    transactionId: NotRequired[str]
    transactionState: Literal[0, 1, 2, 3, 4]
    paymentAmount: NotRequired[float]
    transactionNumber: NotRequired[str]


class ExistingAppointment(TypedDict):
    id: str
    startDateTime: str  # ISO 8601 format
    endDateTime: str  # ISO 8601 format
    number: int
    caseId: NotRequired[str]
    acitivityList: list[Activity]
    customerList: NotRequired[list[Customer]]
    location: BaseLocation
    fieldList: NotRequired[list[Field]]
    message: NotRequired[str]
    creationDateTime: NotRequired[str]  # ISO 8601 format
    paymentStatus: Payment


# Specific to the body of appointment data sent to the API (POST: \appointment)
class AppointmentActivity(TypedDict):
    activityId: str
    amount: int


class AppointmentData(TypedDict):
    id: None
    activityList: list[AppointmentActivity]
    customerList: list[dict[CustomerFields | str, JSONPrimitive]]
    fromDateTime: str
    toDateTime: str
    locationId: str
    message: NotRequired[str]
    fieldList: None
