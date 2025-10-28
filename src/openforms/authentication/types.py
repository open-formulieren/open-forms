from typing import Literal, NotRequired, TypedDict

# Ideally, we wouldn't be importing such specific types, but enums <-> string literals
# typing kinda sucks, since at runtime these values *do* convert into each other.
from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.constants import (
    EIDASAssuranceLevels,
)


class DigiDEntity(TypedDict):
    identifierType: Literal["bsn"]
    identifier: str


class DigiDAuthorizee(TypedDict):
    legalSubject: DigiDEntity


class DigiDContext(TypedDict):
    source: Literal["digid"]
    levelOfAssurance: (
        Literal[
            "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
            "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
            "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
        ]
        | DigiDAssuranceLevels
    )
    authorizee: DigiDAuthorizee


class DigiDService(TypedDict):
    id: str


class DigiDMandate(TypedDict):
    services: list[DigiDService]


class DigiDMachtigenContext(DigiDContext):
    representee: DigiDEntity
    mandate: DigiDMandate


class EHerkenningLegalSubject(TypedDict):
    identifierType: Literal["kvkNummer"]
    identifier: str
    branchNumber: NotRequired[str]


class EHerkenningActingSubject(TypedDict):
    identifierType: Literal["opaque"]
    identifier: str


class EHerkenningAuthorizee(TypedDict):
    legalSubject: EHerkenningLegalSubject
    actingSubject: EHerkenningActingSubject


class EHerkenningContext(TypedDict):
    source: Literal["eherkenning"]
    levelOfAssurance: (
        Literal[
            "urn:etoegang:core:assurance-class:loa1",
            "urn:etoegang:core:assurance-class:loa2",
            "urn:etoegang:core:assurance-class:loa2plus",
            "urn:etoegang:core:assurance-class:loa3",
            "urn:etoegang:core:assurance-class:loa4",
        ]
        | AssuranceLevels
    )
    authorizee: EHerkenningAuthorizee


class EHRepresenteeEntity(TypedDict):
    identifierType: Literal["bsn"]
    identifier: str


class EHMandateService(TypedDict):
    id: str
    uuid: str


class EHMandate(TypedDict):
    role: NotRequired[Literal["bewindvoerder", "curator", "mentor"]]
    services: list[EHMandateService]


class EHerkenningMachtigenContext(EHerkenningContext):
    representee: EHRepresenteeEntity
    mandate: EHMandate


class EmployeeLegalSubject(TypedDict):
    identifierType: Literal["opaque"]
    identifier: str


class EmployeeAuthorizee(TypedDict):
    legalSubject: EmployeeLegalSubject


# This type definition is highly experimental, and will most definitely change
class EmployeeContext(TypedDict):
    source: Literal["custom"]
    levelOfAssurance: Literal["unknown"]
    authorizee: EmployeeAuthorizee


class YiviLegalSubject(TypedDict):
    identifierType: Literal["bsn", "kvkNummer", "opaque"]
    identifier: str
    additionalInformation: dict  # For the additional scoped claims


class YiviAuthorizee(TypedDict):
    legalSubject: YiviLegalSubject


# This type definition is experimental, and will likely change
class YiviContext(TypedDict):
    source: Literal["yivi"]
    # The levelOfAssurance changes based on the used configured auth attribute
    levelOfAssurance: Literal[
        "urn:etoegang:core:assurance-class:loa1",
        "urn:etoegang:core:assurance-class:loa2",
        "urn:etoegang:core:assurance-class:loa2plus",
        "urn:etoegang:core:assurance-class:loa3",
        "urn:etoegang:core:assurance-class:loa4",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
        "unknown",
    ]
    authorizee: YiviAuthorizee


class EIDASNaturalPersonSubject(TypedDict):
    identifierType: Literal["bsn", "opaque"]
    identifier: str
    firstName: str
    familyName: str
    dateOfBirth: str


class EIDASCompanySubject(TypedDict):
    identifierType: Literal["opaque"]
    identifier: str
    companyName: str


class EIDASNaturalPersonAuthorizee(TypedDict):
    legalSubject: EIDASNaturalPersonSubject


class EIDASCompanyAuthorizee(TypedDict):
    legalSubject: EIDASCompanySubject
    actingSubject: EIDASNaturalPersonSubject


class EIDASService(TypedDict):
    id: str


class EIDASMandate(TypedDict):
    services: list[EIDASService]


class EIDASContext(TypedDict):
    source: Literal["eidas"]
    levelOfAssurance: (
        Literal[
            "urn:etoegang:core:assurance-class:loa2",
            "urn:etoegang:core:assurance-class:loa2plus",
            "urn:etoegang:core:assurance-class:loa3",
            "urn:etoegang:core:assurance-class:loa4",
        ]
        | EIDASAssuranceLevels
    )
    authorizee: EIDASNaturalPersonAuthorizee


class EIDASCompanyContext(TypedDict):
    source: Literal["eidas"]
    levelOfAssurance: (
        Literal[
            "urn:etoegang:core:assurance-class:loa2",
            "urn:etoegang:core:assurance-class:loa2plus",
            "urn:etoegang:core:assurance-class:loa3",
            "urn:etoegang:core:assurance-class:loa4",
        ]
        | EIDASAssuranceLevels
    )
    authorizee: EIDASCompanyAuthorizee
    mandate: EIDASMandate


type AnyAuthContext = (
    DigiDContext
    | DigiDMachtigenContext
    | EHerkenningContext
    | EHerkenningMachtigenContext
    | EIDASContext
    | EIDASCompanyContext
    | EmployeeContext
    | YiviContext
)
