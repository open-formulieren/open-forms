from collections.abc import Collection

from django.db import models
from django.utils.translation import gettext_lazy as _


class CitizenAttributes(models.TextChoices):
    legal_identifier = ("legalSubject.identifier", _("Legal subject > Identifier"))
    legal_identifier_type = (
        "legalSubject.identifierType",
        _("Legal subject > Identifier type"),
    )
    legal_first_name = ("legalSubject.firstName", _("Legal subject > First name"))
    legal_family_name = ("legalSubject.familyName", _("Legal subject > Family name"))
    legal_date_of_birth = (
        "legalSubject.dateOfBirth",
        _("Legal subject > Date of birth"),
    )


REQUIRED_CITIZEN_CLIENT_IDENTITY_SETTINGS: Collection[str] = (
    "legal_subject_identifier_claim_path",
    "legal_subject_identifier_type_claim_path",
    "legal_subject_first_name_claim_path",
    "legal_subject_family_name_claim_path",
    "legal_subject_date_of_birth_claim_path",
)


class CompanyAttributes(models.TextChoices):
    legal_identifier = "legalSubject.identifier", _("Legal subject > Identifier")
    legal_company_name = "legalSubject.companyName", _("Legal subject > Company name")

    acting_identifier = "actingSubject.identifier", _("Acting subject > Identifier")
    acting_identifier_type = (
        "actingSubject.identifierType",
        _("Acting subject > Identifier type"),
    )
    acting_first_name = "actingSubject.firstName", _("Acting subject > First name")
    acting_family_name = "actingSubject.familyName", _("Acting subject > Family name")
    acting_date_of_birth = (
        "actingSubject.dateOfBirth",
        _("Acting subject > Date of birth"),
    )


REQUIRED_COMPANY_CLIENT_IDENTITY_SETTINGS: Collection[str] = (
    "legal_subject_identifier_claim_path",
    "legal_subject_name_claim_path",
    "acting_subject_identifier_claim_path",
    "acting_subject_identifier_type_claim_path",
    "acting_subject_first_name_claim_path",
    "acting_subject_family_name_claim_path",
    "acting_subject_date_of_birth_claim_path",
    "mandate_service_id_claim_path",
)
