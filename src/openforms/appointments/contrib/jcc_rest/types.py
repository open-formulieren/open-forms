from typing import Literal, TypedDict


class Revision(TypedDict):
    id: str
    creationDateTime: str  # ISO 8601 format
    creatorAuthenticationUserId: str | None


class PhoneNumber(TypedDict):
    auditId: str
    id: str
    revision: Revision
    value: str | None


class PhoneNumberType(TypedDict):
    auditId: str
    id: str
    revision: Revision
    name: str | None
    description: str | None


class LocationPhoneNumber(TypedDict):
    auditId: str
    id: str
    revision: Revision
    phoneNumber: PhoneNumber
    phoneNumberType: PhoneNumberType


class Country(TypedDict):
    id: str
    isoCode: str | None
    name: str | None


class Address(TypedDict):
    auditId: str
    id: str
    revision: Revision
    department: str | None
    streetName: str | None
    houseNumber: str | None
    houseNumberSuffix: str | None
    postalCode: str | None
    city: str | None
    province: str | None
    country: Country
    customCountryIso: str | None


class BaseLocation(TypedDict):
    id: str
    description: str | None


class Location(BaseLocation):
    auditId: str
    revision: Revision
    isActive: bool | None
    code: str | None
    phoneNumberList: list[LocationPhoneNumber] | None
    address: Address
    synergyId: str | None
    emailAddress: str | None
    isDefault: bool
    smtpFromEmailAddress: str | None
    smtpFromName: str | None
    internetAppointmentBaseUrl: str | None
    locationNumber: int


class CustomerFields(TypedDict):
    # Fields with type Literal[0, 1, 2]
    # 0: visible (it can be submitted without a value)
    # 1: hidden (it's not shown and it's not required)
    # 2: required (should be shown and should have a value)

    auditId: str
    id: str
    revision: Revision
    gender: Literal[0, 1, 2]
    firstName: Literal[0, 1, 2]
    initials: Literal[0, 1, 2]
    # if true both are visible and at least one should be provided
    areFirstNameOrInitialsRequired: bool
    lastNamePrefix: Literal[0, 1, 2]
    birthDate: Literal[0, 1, 2]
    socialSecurityNumber: Literal[0, 1, 2]
    nationality: Literal[0, 1, 2]
    language: Literal[0, 1, 2]
    emailAddress: Literal[0, 1, 2]
    mainPhoneNumber: Literal[0, 1, 2]
    mobilePhoneNumber: Literal[0, 1, 2]
    # if true both are visible and at least one should be provided
    isAnyPhoneNumberRequired: bool
    streetName: Literal[0, 1, 2]
    houseNumber: Literal[0, 1, 2]
    houseNumberSuffix: Literal[0, 1, 2]
    postalCode: Literal[0, 1, 2]
    city: Literal[0, 1, 2]
    country: Literal[0, 1, 2]
    isDefault: bool


class BaseAppointment(TypedDict):
    id: str
    code: int
    message: str | None
    validateErrors: list[str] | None
    acknowledgeIsSuccess: bool
    exception: str | None
    logLevel: Literal[0, 1, 2, 3, 4]


class CreatedAppointment(BaseAppointment):
    pass


class CancelledAppointment(BaseAppointment):
    pass


class Activity(TypedDict):
    id: str
    number: int
    code: str | None
    description: str | None
    necessities: str | None
    appointmentDuration: int
    maxCountForEvent: int | None
    activityGroupId: str | None
    synonyms: list[str] | None


class Customer(TypedDict):
    id: str | None
    isMainCustomer: bool
    gender: Literal[0, 1, 2]  # 0 (None),1 (Man),2 (Woman)
    firstName: str | None
    initials: str | None
    lastNamePrefix: str | None
    lastName: str | None
    birthDate: str | None  # ISO 8601 format
    emailAddress: str | None
    phoneNumber: str | None
    mobilePhoneNumber: str | None
    streetName: str | None
    houseNumber: int | None
    houseNumberSuffix: str | None
    postalCode: str | None
    city: str | None
    socialSecurityNumber: str | None
    ssnCountryId: str | None
    nationalityId: str | None
    customNationality: str | None
    languageId: str | None
    addressCountryId: str | None
    customCountryIso: str | None


class Field(TypedDict):
    id: str
    fileName: str | None
    file: str | None
    value: str | None
    fieldDefinitionId: str


class Payment(TypedDict):
    transactionId: str | None
    transactionState: Literal[0, 1, 2, 3, 4]
    paymentAmount: float | None
    transactionNumber: str | None


class ExistingAppointment(TypedDict):
    id: str
    startDateTime: str  # ISO 8601 format
    endDateTime: str  # ISO 8601 format
    number: int
    caseId: str | None
    acitivityList: list[Activity]
    customerList: list[Customer] | None
    location: BaseLocation
    fieldList: list[Field] | None
    message: str | None
    creationDateTime: str | None  # ISO 8601 format
    paymentStatus: Payment
