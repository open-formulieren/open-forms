from typing import Literal, NotRequired, TypedDict


class MappingItem(TypedDict):
    form_variable: str
    stuf_name: str


class RegistrationOptions(TypedDict):
    zds_zaaktype_code: str
    zds_zaaktype_omschrijving: NotRequired[str]
    zds_zaaktype_status_code: NotRequired[str]
    zds_zaaktype_status_omschrijving: NotRequired[str]
    zds_documenttype_omschrijving_inzending: str
    zds_zaakdoc_vertrouwelijkheid: Literal[
        "ZEER GEHEIM",
        "GEHEIM",
        "CONFIDENTIEEL",
        "VERTROUWELIJK",
        "ZAAKVERTROUWELIJK",
        "INTERN",
        "BEPERKT OPENBAAR",
        "OPENBAAR",
    ]
    variables_mapping: NotRequired[list[MappingItem]]
