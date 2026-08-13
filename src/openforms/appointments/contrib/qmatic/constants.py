from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from openforms.formio.typing import Component


class CustomerFields(TextChoices):
    """
    Enum of possible customer field names offered by Qmatic.

    Documentation reference: "Book an appointment for a selected branch, service, date
    and time" and the "Customer" data model.

    .. note:: None of the customer fields are mandatory, but not providing any information
       makes it impossible to identify a customer.

    The enum values are the fields as they go in the customer record.
    """

    first_name = "firstName", _("First name")  # string, max length 200
    last_name = "lastName", _("Last name")  # string, max length 200
    email = "email", _("Email address")  # string, max length 255
    phone_number = "phone", _("Phone number")  # string, max length 50
    address_line_1 = (
        "addressLine1",
        _("Street name and number"),
    )  # string, max length 255
    address_line_2 = "addressLine2", _("Address line 2")  # string, max length 255
    address_city = "addressCity", _("City")  # string, max length 255
    address_state = "addressState", _("State")  # string, max length 255
    address_zip = "addressZip", _("Postal code")  # string, max length 255
    address_country = "addressCountry", _("Country")  # string, max length 255
    identification_number = (
        "identificationNumber",
        _("Identification number"),
    )  # string, max length 255
    external_id = (
        "externalId",
        _("Unique customer identification/account number"),
    )  # string, max length 255
    """
    A unique customer identification or account number.

    This could be used programmatically, but should not be set by the end-user as it is
    untrusted input.
    """
    birthday = (
        "dateOfBirth",
        _("Birthday"),
    )  # string, ISO-8601 date (return value is number)


FIELD_TO_FORMIO_COMPONENT: dict[str, Component] = {
    CustomerFields.first_name: {
        "id": "68532fc7-e745-4b49-96b8-abdb39728486",
        "type": "textfield",
        "key": CustomerFields.first_name.value,
        "label": CustomerFields.first_name.label,
        "autocomplete": "given-name",
        "validate": {
            "required": True,
            "maxLength": 200,
        },
    },
    CustomerFields.last_name: {
        "id": "6d773462-c8b2-4d71-a691-a095b4f520dc",
        "type": "textfield",
        "key": CustomerFields.last_name.value,
        "label": CustomerFields.last_name.label,
        "autocomplete": "family-name",
        "validate": {
            "required": True,
            "maxLength": 200,
        },
    },
    CustomerFields.email: {
        "id": "515963be-6407-487e-a522-46afd0fc83de",
        "type": "email",
        "key": CustomerFields.email.value,
        "label": CustomerFields.email.label,
        "autocomplete": "email",
        "validate": {
            "required": True,
            "maxLength": 255,
        },
    },
    CustomerFields.phone_number: {
        "id": "c1af01a3-f6bf-45c0-8409-ead5d8bba48b",
        "type": "phoneNumber",
        "key": CustomerFields.phone_number.value,
        "label": CustomerFields.phone_number.label,
        "autocomplete": "tel",
        "validate": {
            "required": True,
            "maxLength": 50,
        },
    },
    CustomerFields.address_line_1: {
        "id": "9c42ff0a-9c3b-4420-a5e0-5c4fd44a99ab",
        "type": "textfield",
        "key": CustomerFields.address_line_1.value,
        "label": CustomerFields.address_line_1.label,
        "autocomplete": "address-line1",
        "validate": {
            "required": True,
            "maxLength": 255,
        },
    },
    CustomerFields.address_line_2: {
        "id": "c5489db9-c4a0-4b70-8d67-a1e34b9c57f9",
        "type": "textfield",
        "key": CustomerFields.address_line_2.value,
        "label": CustomerFields.address_line_2.label,
        "autocomplete": "address-line2",
        "validate": {
            "required": True,
            "maxLength": 255,
        },
    },
    CustomerFields.address_city: {
        "id": "a3e60cff-9e74-476e-b3f4-2a902420a357",
        "type": "textfield",
        "key": CustomerFields.address_city.value,
        "label": CustomerFields.address_city.label,
        "autocomplete": "address-line2",
        "validate": {
            "required": True,
            "maxLength": 255,
        },
    },
    CustomerFields.address_state: {
        "id": "c1be0975-e23d-481f-a472-1bcbb21b8092",
        "type": "textfield",
        "key": CustomerFields.address_state.value,
        "label": CustomerFields.address_state.label,
        "autocomplete": "address-level1",
        "validate": {
            "required": True,
            "maxLength": 255,
        },
    },
    CustomerFields.address_zip: {
        "id": "6212f0a8-68cf-4327-9f22-10f1957f4a93",
        "type": "textfield",
        "key": CustomerFields.address_zip.value,
        "label": CustomerFields.address_zip.label,
        "autocomplete": "postal-code",
        "validate": {
            "required": True,
            "maxLength": 255,
        },
    },
    CustomerFields.address_country: {
        "id": "ba2a596a-600b-41f7-9825-c17dfcc89bce",
        "type": "textfield",
        "key": CustomerFields.address_country.value,
        "label": CustomerFields.address_country.label,
        "autocomplete": "country-name",
        "validate": {
            "required": True,
            "maxLength": 255,
        },
    },
    CustomerFields.identification_number: {
        "id": "11707678-80e5-449d-9d4c-34b22b5216fe",
        "type": "bsn",
        "key": CustomerFields.identification_number.value,
        "label": CustomerFields.identification_number.label,
        "validate": {
            "required": True,
            "maxLength": 255,
        },
    },
    CustomerFields.birthday: {
        "id": "f81eb8c1-1f9b-43b7-b24e-24fcb2d3e049",
        "type": "date",
        "key": CustomerFields.birthday.value,
        "label": CustomerFields.birthday.label,
        "autocomplete": "bday",
        "validate": {
            "required": True,
        },
        "openForms": {
            "widget": "inputGroup",
        },
    },
}


# sanity check
for member in CustomerFields.values:
    if member == CustomerFields.external_id:
        continue
    assert member in FIELD_TO_FORMIO_COMPONENT, (
        f"Missing field '{member}' in FIELD_TO_FORMIO_COMPONENT mapping"
    )
