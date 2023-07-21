from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from openforms.formio.typing import Component, RadioComponent


class CustomerFields(TextChoices):
    """
    Enum of possible customer field names offered by JCC.

    Documentation reference 4.25 GetRequiredClientFields

    .. note:: The field 'last name' is always required and included here for
       completeness sake, but never returned from the service.

    For details about the meaning of fields, see 3.1 AppointmentDetailsType in the
    documentation - that's what the fields map to (with the ``client`` prefix).
    """

    last_name = "LastName", _("Last name")
    """
    Customer last name, max length 128
    """

    address = "Address", _("Address")
    """
    Street name and number - max length 64.
    """

    birthday = "Birthday", _("Birthday")
    """
    Customer date of birth. May not be in the future (assuming this is ``clientDateOfBirth``).
    """

    city = "City", _("City")
    """
    Name of city where customer lives, max length 80.
    """

    email = "Email", _("Email address")
    """
    Contact email address, max length 254 and must be a valid email.
    """

    initials = "Initials", _("Initials")
    """
    Initials (or first name!) of the customer. Max length 128.
    """

    sex = "Sex", _("Sex")
    """
    Gender of the customer, either ``M`` or ``F``.
    """

    main_tel = "MainTel", _("Main phone number")
    """
    Fixed or mobile phone number, max length 16.

    Likely ``clientTel``, can't be used with both main tel and mobile tel.
    """

    mobile_tel = "MobileTel", _("Mobile phone number")
    """
    Mobile phone number, max length 16.

    Likely ``clientTel``, can't be used with both main tel and mobile tel.
    """

    any_tel = "AnyTel", _("AnyTel")  # uh... no idea if/how this maps.

    postal_code = "PostalCode", _("Postal code")
    """
    Postal code, max length 16.
    """

    ID = "ID", _("ID")
    """
    SSN of the customer, like BSN or Rijksregisternummer (BE). Max length 16.
    """


_GENDER_FIELD: RadioComponent = {
    "type": "radio",
    "key": CustomerFields.sex.value,
    "label": CustomerFields.sex.label,
    "validate": {
        "required": True,
    },
    "values": [
        {"value": "M", "label": _("Male")},  # type: ignore (can't handle the gettext_lazy return type)
        {"value": "F", "label": _("Female")},  # type: ignore (can't handle the gettext_lazy return type)
    ],
}


FIELD_TO_FORMIO_COMPONENT: dict[CustomerFields, Component] = {
    CustomerFields.last_name: {
        "type": "textfield",
        "key": CustomerFields.last_name.value,
        "label": CustomerFields.last_name.label,
        "autocomplete": "family-name",
        "validate": {
            "required": True,
            "maxLength": 128,
        },
    },
    CustomerFields.address: {
        "type": "textfield",
        "key": CustomerFields.address.value,
        "label": CustomerFields.address.label,
        "autocomplete": "address-line1",
        "validate": {
            "required": True,
            "maxLength": 64,
        },
    },
    CustomerFields.birthday: {
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
    CustomerFields.city: {
        "type": "textfield",
        "key": CustomerFields.city.value,
        "label": CustomerFields.city.label,
        "autocomplete": "address-line2",
        "validate": {
            "required": True,
            "maxLength": 80,
        },
    },
    CustomerFields.email: {
        "type": "email",
        "key": CustomerFields.email.value,
        "label": CustomerFields.email.label,
        "autocomplete": "email",
        "validate": {
            "required": True,
            "maxLength": 254,
        },
    },
    CustomerFields.initials: {
        "type": "textfield",
        "key": CustomerFields.initials.value,
        "label": CustomerFields.initials.label,
        "autocomplete": "given-name",
        "validate": {
            "required": True,
            "maxLength": 128,
        },
    },
    CustomerFields.sex: _GENDER_FIELD,
    CustomerFields.main_tel: {
        "type": "phoneNumber",
        "key": CustomerFields.main_tel.value,
        "label": CustomerFields.main_tel.label,
        "autocomplete": "tel",
        "validate": {
            "required": True,
            "maxLength": 16,
        },
    },
    CustomerFields.mobile_tel: {
        "type": "phoneNumber",
        "key": CustomerFields.mobile_tel.value,
        "label": CustomerFields.mobile_tel.label,
        "autocomplete": "tel",
        "validate": {
            "required": True,
            "maxLength": 16,
        },
    },
    CustomerFields.any_tel: {
        "type": "phoneNumber",
        "key": CustomerFields.any_tel.value,
        "label": CustomerFields.any_tel.label,
        "autocomplete": "tel",
        "validate": {
            "required": True,
            "maxLength": 16,
        },
    },
    CustomerFields.postal_code: {
        "type": "textfield",
        "key": CustomerFields.postal_code.value,
        "label": CustomerFields.postal_code.label,
        "autocomplete": "postal-code",
        "validate": {
            "required": True,
            "maxLength": 16,
        },
    },
    CustomerFields.ID: {
        "type": "bsn",
        "key": CustomerFields.ID.value,
        "label": CustomerFields.ID.label,
        "validate": {
            "required": True,
            "maxLength": 16,
        },
    },
}

FIELD_TO_XML_NAME: dict[CustomerFields, str] = {
    CustomerFields.last_name: "clientLastName",
    CustomerFields.address: "clientAddress",
    CustomerFields.birthday: "clientDateOfBirth",
    CustomerFields.city: "clientCity",
    CustomerFields.email: "clientMail",
    CustomerFields.initials: "clientInitials",
    CustomerFields.sex: "clientSex",
    CustomerFields.main_tel: "clientTel",
    CustomerFields.mobile_tel: "clientTel",
    CustomerFields.any_tel: "clientTel",
    CustomerFields.postal_code: "clientPostalCode",
    CustomerFields.ID: "clientID",
}

# sanity checks
for member in CustomerFields.values:
    assert (
        member in FIELD_TO_FORMIO_COMPONENT
    ), f"Missing field '{member}' in FIELD_TO_FORMIO_COMPONENT mapping"
    assert (
        member in FIELD_TO_XML_NAME
    ), f"Missing field '{member}' in FIELD_TO_XML_NAME mapping"
