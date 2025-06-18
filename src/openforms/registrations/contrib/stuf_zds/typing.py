from typing import Literal, NotRequired, TypedDict


class MappingItem(TypedDict):
    form_variable: str
    stuf_name: str


class VariablesMapping(TypedDict):
    variable_key: str
    register_as: Literal["zaakbetrokkene", "extraElementen"]
    description: NotRequired[str]


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
    payment_status_update_mapping: NotRequired[list[MappingItem]]
    variables_mapping: NotRequired[list[VariablesMapping]]
