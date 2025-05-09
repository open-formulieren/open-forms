from openforms.contrib.haal_centraal.clients.brp import NaturalPersonDetails


def covert_to_json_serializable(data: dict[str, list[NaturalPersonDetails]]):
    serializable_data = {
        key: {
            inner_key: [child.model_dump() for child in inner_value]
            for inner_key, inner_value in value.items()
        }
        for key, value in data.items()
    }
    return serializable_data
