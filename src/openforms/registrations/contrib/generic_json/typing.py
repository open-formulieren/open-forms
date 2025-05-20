from typing import TypedDict

from zgw_consumers.models import Service


class GenericJSONOptions(TypedDict):
    """
    Generic JSON registration plugin options

    This describes the shape of :attr:`GenericJSONOptionsSerializer.validated_data`,
    after the input data has been cleaned/validated.
    """

    service: Service
    path: str
    variables: list[str]
    fixed_metadata_variables: list[str]
    additional_metadata_variables: list[str]
    transform_to_list: list[str]
