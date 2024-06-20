from typing import Literal, TypedDict


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
