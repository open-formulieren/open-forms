from zgw_consumers.nlx import NLXClient

CRS_HEADERS = {"Content-Crs": "EPSG:4326"}


class ObjectsClient(NLXClient):
    def create_object(self, objecttype_url: str, record_data: dict) -> dict:

        json = {
            "type": objecttype_url,
            "record": record_data,
        }

        response = self.post("objects", json=json, headers=CRS_HEADERS)
        response.raise_for_status()

        return response.json()
