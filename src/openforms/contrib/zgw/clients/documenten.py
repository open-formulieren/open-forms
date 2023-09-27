from zgw_consumers_ext.api_client import NLXClient

ENDPOINT_MAP = {
    "enkelvoudiginformatieobject": "enkelvoudiginformatieobjecten",
}


class DocumentenClient(NLXClient):

    # TEMPORARY implementation while we refactor the API clients & satisfying the type
    # checkers.

    def list(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def create(self, resource: str, data: dict, **kwargs) -> dict:
        endpoint = ENDPOINT_MAP[resource]
        response = self.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    def partial_update(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError
