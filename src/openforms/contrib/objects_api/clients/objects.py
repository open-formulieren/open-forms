from zgw_consumers.nlx import NLXClient

CRS_HEADERS = {"Content-Crs": "EPSG:4326"}


class ObjectsClient(NLXClient):
    def create_object(self, object_data: dict) -> dict:
        response = self.post("objects", json=object_data, headers=CRS_HEADERS)
        response.raise_for_status()

        return response.json()
