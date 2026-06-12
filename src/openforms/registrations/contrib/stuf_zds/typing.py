from collections.abc import Collection
from typing import Literal, NotRequired, TypedDict


class MappingItem(TypedDict):
    form_variable: str
    stuf_name: str
    serialize_list_to_csv: NotRequired[bool]
    """
    If enabled, list values will be serialized as a comma separated string value.
    """


class FileComponentOptions(TypedDict):
    key: str
    title: NotRequired[str]


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
    variables_mapping_initiator: NotRequired[list[MappingItem]]
    files: NotRequired[Collection[FileComponentOptions]]
    """
    List of file upload options for the Documents API.

    Each item contains at least the Formio component ``key`` key, which can contain
    ``.`` characters. It's the literal key string as defined on the component.

    Keys may refer to file components inside editgrid components too. We rely on the
    admin enforcing key uniqueness for *all* components in the form, which is stricter
    than vanilla Formio.
    """
