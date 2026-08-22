from django.db.models import IntegerChoices, TextChoices
from django.utils.translation import gettext_lazy as _

from openforms.formio.constants import DataSrcOptions
from openforms.formio.typing import Component


class GenderType(TextChoices):
    other = "0", _("Other")
    male = "1", _("Male")
    female = "2", _("Female")


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
        "id": "ca615f88-e579-4c0c-b98a-b9306baf0182",
        "type": "radio",
        "key": CustomerFields.gender.value,
        "label": CustomerFields.gender.label,
        "validate": {},
        "values": [  # pyright: ignore[reportAssignmentType]
            {"value": str(GenderType.male.value), "label": GenderType.male.label},
            {"value": str(GenderType.female.value), "label": GenderType.female.label},
            {"value": str(GenderType.other.value), "label": GenderType.other.label},
        ],
        "openForms": {"dataSrc": DataSrcOptions.manual},
    },
    CustomerFields.first_name: {
        "id": "40f16215-df91-4799-98e2-af7fad562942",
        "type": "textfield",
        "key": CustomerFields.first_name.value,
        "label": CustomerFields.first_name.label,
        "autocomplete": "first-name",
        "validate": {
            "maxLength": 128,
        },
    },
    CustomerFields.initials: {
        "id": "8ee54b5d-1553-4e22-a15a-ff8cd18deb34",
        "type": "textfield",
        "key": CustomerFields.initials.value,
        "label": CustomerFields.initials.label,
        "autocomplete": "initials",
        "validate": {
            "maxLength": 128,
        },
    },
    CustomerFields.last_name: {
        "id": "b66d5a44-2dc1-4136-a831-c25760b632e3",
        "type": "textfield",
        "key": CustomerFields.last_name.value,
        "label": CustomerFields.last_name.label,
        "autocomplete": "family-name",
        "validate": {
            "maxLength": 128,
            "required": True,
        },
    },
    CustomerFields.last_name_prefix: {
        "id": "538ddcc3-1f0a-49b1-8e46-b801cfb76723",
        "type": "textfield",
        "key": CustomerFields.last_name_prefix.value,
        "label": CustomerFields.last_name_prefix.label,
        "autocomplete": "family-name-prefix",
        "validate": {
            "maxLength": 128,
        },
    },
    CustomerFields.date_of_birth: {
        "id": "bcb0b78b-e8d0-4ad9-a0cd-dc7cbb996bc7",
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
        "id": "af5c2881-a5c6-48dd-b15a-1d191bb79ece",
        "type": "textfield",
        "key": CustomerFields.social_security_number.value,
        "label": CustomerFields.social_security_number.label,
        "autocomplete": "social-security-number",
        "validate": {
            "maxLength": 16,
        },
    },
    CustomerFields.nationality: {
        "id": "78fdbbda-22c4-4ea5-8c53-df1652ae57fc",
        "type": "textfield",
        "key": CustomerFields.nationality.value,
        "label": CustomerFields.nationality.label,
        "autocomplete": "nationality",
        "validate": {
            "maxLength": 128,
        },
    },
    CustomerFields.language: {
        "id": "b7a099d9-24a1-4e50-ba51-c6d7a61608ed",
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
        "id": "816e74d4-ac1b-4fa9-93a8-f6857aecec50",
        "type": "email",
        "key": CustomerFields.email_address.value,
        "label": CustomerFields.email_address.label,
        "autocomplete": "email-address",
        "validate": {
            "maxLength": 254,
        },
    },
    CustomerFields.phone_number: {
        "id": "b43d624e-0a64-43a8-9b59-70d4945748b1",
        "type": "phoneNumber",
        "key": CustomerFields.phone_number.value,
        "label": CustomerFields.phone_number.label,
        "autocomplete": "phone-number",
        "validate": {},
    },
    CustomerFields.mobile_phone_number: {
        "id": "a6a480d8-0a99-4192-bf19-5716a15460b8",
        "type": "phoneNumber",
        "key": CustomerFields.mobile_phone_number.value,
        "label": CustomerFields.mobile_phone_number.label,
        "autocomplete": "mobile-phone-number",
        "validate": {
            "maxLength": 16,
        },
    },
    CustomerFields.street_name: {
        "id": "c0b7101a-f36d-4a19-a3e5-01ded4f3aa98",
        "type": "textfield",
        "key": CustomerFields.street_name.value,
        "label": CustomerFields.street_name.label,
        "autocomplete": "street-name",
        "validate": {
            "maxLength": 64,
        },
    },
    CustomerFields.house_number: {
        "id": "81735f6a-1408-4b8d-b3dd-488a9433499b",
        "type": "textfield",
        "key": CustomerFields.house_number.value,
        "label": CustomerFields.house_number.label,
        "autocomplete": "house-number",
        "validate": {},
    },
    CustomerFields.house_number_suffix: {
        "id": "3b383366-9d6d-4bde-b6a8-660e5399ad34",
        "type": "textfield",
        "key": CustomerFields.house_number_suffix.value,
        "label": CustomerFields.house_number_suffix.label,
        "autocomplete": "house-number-suffix",
        "validate": {},
    },
    CustomerFields.postcode: {
        "id": "6a53d3eb-5915-4b2e-842c-d2964791b40c",
        "type": "textfield",
        "key": CustomerFields.postcode.value,
        "label": CustomerFields.postcode.label,
        "autocomplete": "postcode",
        "validate": {
            "maxLength": 16,
        },
    },
    CustomerFields.city: {
        "id": "370af760-306d-4676-a4f8-a455bb193d19",
        "type": "textfield",
        "key": CustomerFields.city.value,
        "label": CustomerFields.city.label,
        "autocomplete": "city",
        "validate": {
            "maxLength": 80,
        },
    },
    CustomerFields.country: {
        "id": "a0aee360-27d9-4193-a071-a57e28dee153",
        "type": "textfield",
        "key": CustomerFields.country.value,
        "label": CustomerFields.country.label,
        "autocomplete": "country",
        "validate": {
            "maxLength": 80,
        },
    },
}


# Make sure we do not miss any field in the components definition
for member in CustomerFields.values:
    assert member in FIELD_TO_FORMIO_COMPONENT, (
        f"Missing field '{member}' in FIELD_TO_FORMIO_COMPONENT mapping"
    )
