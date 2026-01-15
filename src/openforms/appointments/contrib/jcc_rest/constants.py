from copy import deepcopy

from django.db.models import IntegerChoices, TextChoices
from django.utils.translation import gettext_lazy as _

from openforms.formio.typing import Component


class GenderType(IntegerChoices):
    other = 0, _("Other")
    male = 1, _("Male")
    female = 2, _("Female")


class FieldState(IntegerChoices):
    visible = 0, _("Visible")
    hidden = 1, _("Hidden")
    required = 2, _("Required")


class CustomerFields(TextChoices):
    """
    Enum of possible customer field names offered by JCC Rest.

    Documentation references:
        - https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/API/

    """

    # JCC treats gender with the values 0 (None),1 (Man),2 (Woman)
    gender = "gender", _("Gender")
    """
    Customer's Gender, one of Other (0), Male (1) or Female (2).
    """

    first_name = "firstName", _("First name")
    """
    Customer's first name, max length 128.
    """

    initials = "initials", _("Initials")
    """
    Customer's initials, max length 128.
    """

    last_name = "lastName", _("Last name")
    """
    Customer's last name, max length 128.
    """

    last_name_prefix = "lastNamePrefix", _("Last name prefix")
    """
    Customer's last name prefix, max length 128.
    """

    date_of_birth = "birthDate", _("Date of birth")
    """
    Customer's date of birth. Datetime string ("2019-08-24T14:15:22Z").
    """

    social_security_number = "socialSecurityNumber", _("Social security number")
    """
    Customer's social security number like BSN, max length 16.
    """

    nationality = "nationality", _("Nationality")
    """
    Customer's nationality, max length 128.
    """

    language = "language", _("Language")
    """
    Customer's language, max length 128.
    """

    email_address = "emailAddress", _("Email address")
    """
    Contact email address, max length 254.
    """

    phone_number = "phoneNumber", _("Phone number")
    """
    Main phone number.
    """

    mobile_phone_number = "mobilePhoneNumber", _("Mobile phone number")
    """
    Mobile phone number, max length 16.
    """

    street_name = "streetName", _("Street name")
    """
    Name of the street where customer lives, max length 64.
    """

    house_number = "houseNumber", _("House number")
    """
    Number of the house where customer lives.
    """

    house_number_suffix = "houseNumberSuffix", _("House number suffix")
    """
    Suffix of the house number where customer lives.
    """

    postcode = "postalCode", _("Postcode")
    """
    Postcode of the region where customer lives, max length 16.
    """

    city = "city", _("City")
    """
    Name of the city where customer lives, max length 80.
    """

    country = "country", _("Country")
    """
    Name of the country where customer lives in, max length 80.
    """


FIELD_TO_FORMIO_COMPONENT: dict[CustomerFields, Component] = {
    CustomerFields.gender: {
        "type": "radio",
        "key": CustomerFields.gender.value,
        "label": CustomerFields.gender.label,
        "validate": {},
        "values": [  # pyright: ignore[reportAssignmentType]
            {"value": GenderType.other, "label": _("Other")},
            {"value": GenderType.male, "label": _("Male")},
            {"value": GenderType.female, "label": _("Female")},
        ],
    },
    CustomerFields.first_name: {
        "type": "textfield",
        "key": CustomerFields.first_name.value,
        "label": CustomerFields.first_name.label,
        "autocomplete": "first-name",
        "validate": {
            "maxLength": 128,
        },
    },
    CustomerFields.initials: {
        "type": "textfield",
        "key": CustomerFields.initials.value,
        "label": CustomerFields.initials.label,
        "autocomplete": "initials",
        "validate": {
            "maxLength": 128,
        },
    },
    CustomerFields.last_name: {
        "type": "textfield",
        "key": CustomerFields.last_name.value,
        "label": CustomerFields.last_name.label,
        "autocomplete": "family-name",
        "validate": {
            "maxLength": 128,
        },
    },
    CustomerFields.last_name_prefix: {
        "type": "textfield",
        "key": CustomerFields.last_name_prefix.value,
        "label": CustomerFields.last_name_prefix.label,
        "autocomplete": "family-name-prefix",
        "validate": {
            "maxLength": 128,
        },
    },
    CustomerFields.date_of_birth: {
        "type": "date",
        "key": CustomerFields.date_of_birth.value,
        "label": CustomerFields.date_of_birth.label,
        "autocomplete": "date-of-birth",
        "validate": {},
        "openForms": {
            "widget": "inputGroup",
        },
    },
    CustomerFields.social_security_number: {
        "type": "textfield",
        "key": CustomerFields.social_security_number.value,
        "label": CustomerFields.social_security_number.label,
        "autocomplete": "social-security-number",
        "validate": {
            "maxLength": 16,
        },
    },
    CustomerFields.nationality: {
        "type": "textfield",
        "key": CustomerFields.nationality.value,
        "label": CustomerFields.nationality.label,
        "autocomplete": "nationality",
        "validate": {
            "maxLength": 128,
        },
    },
    CustomerFields.language: {
        "type": "textfield",
        "key": CustomerFields.language.value,
        "label": CustomerFields.language.label,
        "autocomplete": "language",
        "validate": {
            "maxLength": 128,
        },
    },
    # JCC does have a validation in email address
    CustomerFields.email_address: {
        "type": "email",
        "key": CustomerFields.email_address.value,
        "label": CustomerFields.email_address.label,
        "autocomplete": "email-address",
        "validate": {
            "maxLength": 254,
        },
    },
    CustomerFields.phone_number: {
        "type": "phoneNumber",
        "key": CustomerFields.phone_number.value,
        "label": CustomerFields.phone_number.label,
        "autocomplete": "phone-number",
        "validate": {},
    },
    CustomerFields.mobile_phone_number: {
        "type": "phoneNumber",
        "key": CustomerFields.mobile_phone_number.value,
        "label": CustomerFields.mobile_phone_number.label,
        "autocomplete": "mobile-phone-number",
        "validate": {
            "maxLength": 16,
        },
    },
    CustomerFields.street_name: {
        "type": "textfield",
        "key": CustomerFields.street_name.value,
        "label": CustomerFields.street_name.label,
        "autocomplete": "street-name",
        "validate": {
            "maxLength": 64,
        },
    },
    CustomerFields.house_number: {
        "type": "textfield",
        "key": CustomerFields.house_number.value,
        "label": CustomerFields.house_number.label,
        "autocomplete": "house-number",
        "validate": {},
    },
    CustomerFields.house_number_suffix: {
        "type": "textfield",
        "key": CustomerFields.house_number_suffix.value,
        "label": CustomerFields.house_number_suffix.label,
        "autocomplete": "house-number-suffix",
        "validate": {},
    },
    CustomerFields.postcode: {
        "type": "textfield",
        "key": CustomerFields.postcode.value,
        "label": CustomerFields.postcode.label,
        "autocomplete": "postcode",
        "validate": {
            "maxLength": 16,
        },
    },
    CustomerFields.city: {
        "type": "textfield",
        "key": CustomerFields.city.value,
        "label": CustomerFields.city.label,
        "autocomplete": "city",
        "validate": {
            "maxLength": 80,
        },
    },
    CustomerFields.country: {
        "type": "textfield",
        "key": CustomerFields.country.value,
        "label": CustomerFields.country.label,
        "autocomplete": "country",
        "validate": {
            "maxLength": 80,
        },
    },
}


def get_component(component_type: CustomerFields, required: bool) -> Component:
    component = deepcopy(FIELD_TO_FORMIO_COMPONENT[component_type])
    component.get("validate", {})["required"] = required
    return component


# Make sure we do not miss any field in the components definition
for member in CustomerFields.values:
    assert member in FIELD_TO_FORMIO_COMPONENT, (
        f"Missing field '{member}' in FIELD_TO_FORMIO_COMPONENT mapping"
    )
