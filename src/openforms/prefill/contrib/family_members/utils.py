from typing import Any, Mapping, Sequence

from openforms.contrib.haal_centraal.clients.brp import NaturalPersonDetails


def convert_to_json_serializable(
    data: Mapping[str, Sequence[NaturalPersonDetails]],
) -> dict[str, list[Any]]:
    serializable_data = {
        person_type: [person.model_dump() for person in persons]
        for person_type, persons in data.items()
    }
    return serializable_data
