from django.db import models
from django.utils.translation import gettext_lazy as _

FORM_AUTH_SESSION_KEY = "form_auth"
FORM_AUTH_BACKEND_SESSION_KEY = "form_auth_backend"
REGISTRATOR_SUBJECT_SESSION_KEY = "registrator_subject"

CO_SIGN_PARAMETER = "coSignSubmission"


class AuthAttribute(models.TextChoices):
    """
    core identifying attributes retrieved from the authentication plugins
    """

    bsn = "bsn", _("BSN")
    kvk = "kvk", _("KvK number")
    pseudo = "pseudo", _("Pseudo ID")
    employee_id = "employee_id", _("Employee ID")

    # For eIDAS (via OIDC) we support additional ID types for the legal subject
    national_id = "national_id", _("National ID")
    rsin = "rsin", _("RSIN")
    vat = "vat", _("VAT number")
    lei = "lei", _("Legal Entity Identifier")
    eori = "eori", _("Economic Operators Registration and Identification number")
    ntr = "ntr", _("National Trade Register")


class LogoAppearance(models.TextChoices):
    dark = "dark", _("Dark")
    light = "light", _("Light")


class ModeChoices(models.TextChoices):
    citizen = "citizen", _("Citizen")
    company = "company", _("Company")
    employee = "employee", _("Employee")


class ActingSubjectIdentifierType(models.TextChoices):
    opaque = "opaque", _("Opaque")

    # For eIDAS (via OIDC) we support additional ID types for the acting subject
    national_id = "national_id", _("National ID")
    bsn = "bsn", _("BSN")


class LegalSubjectIdentifierType(models.TextChoices):
    bsn = "bsn", _("BSN")
    kvk = "kvk", _("KvK number")
    rsin = "rsin", _("RSIN")

    # For eIDAS (via OIDC) we support additional ID types for the legal subject
    national_id = "national_id", _("National ID")
    vat = "vat", _("VAT number")
    lei = "lei", _("Legal Entity Identifier")
    eori = "eori", _("Economic Operators Registration and Identification number")
    ntr = "ntr", _("National Trade Register")
    opaque = "opaque", _("Opaque")
