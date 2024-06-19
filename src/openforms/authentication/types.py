from typing import Literal, TypedDict


class DigiDLegalSubject(TypedDict):
    identifierType: Literal["bsn"]
    identifier: str


class DigiDAuthorizee(TypedDict):
    legalSubject: DigiDLegalSubject


class DigiDContext(TypedDict):
    source: Literal["digid"]
    levelOfAssurance: Literal[
        "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
        "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
    ]
    authorizee: DigiDAuthorizee
