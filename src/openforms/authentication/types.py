from typing import Literal, NotRequired, TypedDict


class DigiDEntity(TypedDict):
    identifierType: Literal["bsn"]
    identifier: str


class DigiDAuthorizee(TypedDict):
    legalSubject: DigiDEntity


class DigiDContext(TypedDict):
    source: Literal["digid"]
    levelOfAssurance: Literal[
        "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
    ]
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
    levelOfAssurance: Literal[
        "urn:etoegang:core:assurance-class:loa1",
        "urn:etoegang:core:assurance-class:loa2",
        "urn:etoegang:core:assurance-class:loa2plus",
        "urn:etoegang:core:assurance-class:loa3",
        "urn:etoegang:core:assurance-class:loa4",
    ]
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


# This type definition is highly experimental, and will most definitely change
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


class EIDASLegalSubject(TypedDict):
    identifierType: Literal["bsn"]
    identifier: str


class EIDASActingSubject(TypedDict):
    identifierType: Literal["opaque"]
    identifier: str


class EIDASAuthorizee(TypedDict):
    legalSubject: NotRequired[EIDASLegalSubject]
    actingSubject: EIDASActingSubject


class EIDASContext(TypedDict):
    source: Literal["eidas"]
    levelOfAssurance: Literal[
        "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
    ]
    authorizee: EIDASAuthorizee
