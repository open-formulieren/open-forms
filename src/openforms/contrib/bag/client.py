from .models import BAGConfig


class BAGClient:
    @staticmethod
    def get_address(postcode, house_number):
        config = BAGConfig.get_solo()
        client = config.bag_service.build_client()
        data = {"huisnummer": house_number, "postcode": postcode.replace(' ', '')}
        response = client.operation(
            "bevraagAdressen",
            {},
            method="GET",
            request_kwargs=dict(
                params=data,
                headers={"Accept": "application/hal+json"},
            ),
        )
        if "_embedded" not in response:
            # No addresses were found
            return {}

        address_data = response["_embedded"]["adressen"][0]
        address_data["street_name"] = address_data.pop("korteNaam")
        address_data["city"] = address_data.pop("woonplaatsNaam")
        return address_data
