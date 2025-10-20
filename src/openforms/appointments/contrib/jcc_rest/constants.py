from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from openforms.formio.typing import Component, RadioComponent


class CustomerFields(TextChoices):
    """
    Enum of possible customer field names offered by JCC Rest.

    Documentation references:
        - https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html#tag/WARPAppointment/paths/~1api~1warp~1v1~1appointment/post
        - https://cloud-acceptatie.jccsoftware.nl/JCC/JCC_Leveranciers_Acceptatie/G-Plan/api/api-docs-v1/index.html#tag/WARPCustomer/paths/~1api~1warp~1v1~1customer~1customerfields~1required/get

    """

    gender = "gender", _("Gender")
    # TODO
    # Find out what is the meaning of the 0,1,2 in gender field when we have a POST request
    # for creating an appointment
    """
    Customer's Gender, either ``M``, ``F`` or ``O``.
    """

    first_name = "firstName", _("First name")
    """
    Customer's first name, string or null.
    """

    initials = "initials", _("Initials")
    """
    Customer's initials, string or null.
    """

    last_name = "lastName", _("Last name")
    """
    Customer's last name, string or null.
    """

    last_name_prefix = "lastNamePrefix", _("Last name prefix")
    """
    Customer's last name prefix, string or null.
    """

    date_of_birth = "birthDate", _("Date of birth")
    """
    Customer's date of birth. Datetime string ("2019-08-24T14:15:22Z").
    """

    social_security_number = "socialSecurityNumber", _("Social security number")
    """
    Customer's social security number like BSN, string or null .
    """

    email_address = "emailAddress", _("Email address")
    """
    Contact email address, string or null.
    """

    phone_number = "mainPhoneNumber", _("Phone number")
    """
    Main phone number, string or null.
    """

    mobile_phone_number = "mobilePhoneNumber", _("Mobile phone number")
    """
    Mobile phone number, string or null.
    """

    street_name = "streetName", _("Street name")
    """
    Name of the street where customer lives, string or null.
    """

    house_number = "houseNumber", _("House number")
    """
    Number of the house where customer lives, integer or null.
    """

    house_number_suffix = "houseNumberSuffix", _("House number suffix")
    """
    Suffix of the house number where customer lives, string or null.
    """

    postcode = "postalCode", _("Postcode")
    """
    Postcode of the region where customer lives, string or null.
    """

    city = "city", _("City")
    """
    Name of the city where customer lives, string or null.
    """

    # TODO
    # Fields not returned by the /customer/customerfields/required endpoint but exist in
    # the POST /appointment request.

    # nationalityId = "NationalityId", _("Nationality id")
    # languageId = "LanguageId", _("Language id")
    # isMainCustomer = "IsMainCustomer", _("Is main customer")
    # lastName = "LastName", _("Last name")
    # phoneNumber = "PhoneNumber", _("Phone number")
    # ssnCountryId = "SsnCountryId", _("Social security number id")
    # customNationality = "CustomNationality", _("Custom nationality")
    # addressCountryId = "addressCountryId", _("Address country id")
    # customCountryIso = "customCountryIso", _("Custom country ISO")


_GENDER_FIELD: RadioComponent = {
    "type": "radio",
    "key": CustomerFields.gender.value,
    "label": CustomerFields.gender.label,
    "validate": {
        "required": True,
    },
    "values": [
        {"value": "M", "label": _("Male")},  # type: ignore (can't handle the gettext_lazy return type)
        {"value": "F", "label": _("Female")},  # type: ignore (can't handle the gettext_lazy return type)
    ],
}

FIELD_TO_FORMIO_COMPONENT: dict[CustomerFields, Component] = {
    CustomerFields.gender: _GENDER_FIELD,
    CustomerFields.first_name: {
        "type": "textfield",
        "key": CustomerFields.first_name.value,
        "label": CustomerFields.first_name.label,
        "autocomplete": "first-name",
        "validate": {
            "required": True,
            # "maxLength": 128,
        },
    },
    CustomerFields.initials: {
        "type": "textfield",
        "key": CustomerFields.initials.value,
        "label": CustomerFields.initials.label,
        "autocomplete": "initials",
        "validate": {
            "required": True,
            # "maxLength": 128,
        },
    },
    CustomerFields.last_name: {
        "type": "textfield",
        "key": CustomerFields.last_name.value,
        "label": CustomerFields.last_name.label,
        "autocomplete": "family-name",
        "validate": {
            "required": True,
            # "maxLength": 128,
        },
    },
    CustomerFields.last_name_prefix: {
        "type": "textfield",
        "key": CustomerFields.last_name_prefix.value,
        "label": CustomerFields.last_name_prefix.label,
        "autocomplete": "family-name-prefix",
        "validate": {
            "required": True,
            # "maxLength": 128,
        },
    },
    CustomerFields.date_of_birth: {
        "type": "date",
        "key": CustomerFields.date_of_birth.value,
        "label": CustomerFields.date_of_birth.label,
        "autocomplete": "date-of-birth",
        "validate": {
            "required": True,
        },
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
            "required": True,
        },
    },
    CustomerFields.email_address: {
        "type": "email",
        "key": CustomerFields.email_address.value,
        "label": CustomerFields.email_address.label,
        "autocomplete": "email-address",
        "validate": {
            "required": True,
            # "maxLength": 254,
        },
    },
    CustomerFields.phone_number: {
        "type": "phoneNumber",
        "key": CustomerFields.phone_number.value,
        "label": CustomerFields.phone_number.label,
        "autocomplete": "phone-number",
        "validate": {
            "required": True,
            # "maxLength": 16,
        },
    },
    CustomerFields.mobile_phone_number: {
        "type": "phoneNumber",
        "key": CustomerFields.mobile_phone_number.value,
        "label": CustomerFields.mobile_phone_number.label,
        "autocomplete": "mobile-phone-number",
        "validate": {
            "required": True,
            # "maxLength": 16,
        },
    },
    CustomerFields.street_name: {
        "type": "textfield",
        "key": CustomerFields.street_name.value,
        "label": CustomerFields.street_name.label,
        "autocomplete": "street-name",
        "validate": {
            "required": True,
            # "maxLength": 80,
        },
    },
    CustomerFields.house_number: {
        "type": "textfield",
        "key": CustomerFields.house_number.value,
        "label": CustomerFields.house_number.label,
        "autocomplete": "house-number",
        "validate": {
            "required": True,
            # "maxLength": 80,
        },
    },
    CustomerFields.house_number_suffix: {
        "type": "textfield",
        "key": CustomerFields.house_number_suffix.value,
        "label": CustomerFields.house_number_suffix.label,
        "autocomplete": "house-number-suffix",
        "validate": {
            "required": True,
            # "maxLength": 80,
        },
    },
    CustomerFields.postcode: {
        "type": "textfield",
        "key": CustomerFields.postcode.value,
        "label": CustomerFields.postcode.label,
        "autocomplete": "postcode",
        "validate": {
            "required": True,
            # "maxLength": 16,
        },
    },
    CustomerFields.city: {
        "type": "textfield",
        "key": CustomerFields.city.value,
        "label": CustomerFields.city.label,
        "autocomplete": "city",
        "validate": {
            "required": True,
            # "maxLength": 80,
        },
    },
}


# sanity checks
for member in CustomerFields.values:
    assert member in FIELD_TO_FORMIO_COMPONENT, (
        f"Missing field '{member}' in FIELD_TO_FORMIO_COMPONENT mapping"
    )
