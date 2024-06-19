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
