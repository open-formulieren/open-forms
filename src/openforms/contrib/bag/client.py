from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import elasticapm
from requests import HTTPError
from zds_client import ClientError

from openforms.plugins.exceptions import InvalidPluginConfiguration

from .models import BAGConfig


class BAGClient:
    verbose_name = _("BAG")

    @classmethod
    def make_request(cls, client, data):
        return client.operation(
            "bevraagAdressen",
            {},
            method="GET",
            request_kwargs=dict(
                params=data,
                headers={"Accept": "application/hal+json"},
            ),
        )

    @classmethod
    @elasticapm.capture_span(span_type="app.bag.query")
    def get_address(cls, postcode, house_number):
        config = BAGConfig.get_solo()
        client = config.bag_service.build_client()
        data = {"huisnummer": house_number, "postcode": postcode.replace(" ", "")}

        try:
            response = cls.make_request(client, data)
        except ClientError:
            return {}

        if "_embedded" not in response:
            # No addresses were found
            return {}

        address_data = response["_embedded"]["adressen"][0]
        address_data["street_name"] = address_data.pop("korteNaam")
        address_data["city"] = address_data.pop("woonplaatsNaam")
        return address_data

    @classmethod
    def check_config(cls):
        check_house_number = "1000AA"
        check_postal = "1000AA"

        config = BAGConfig.get_solo()
        if not config.bag_service:
            raise InvalidPluginConfiguration(
                _("{api_name} endpoint is not configured.").format(
                    api_name="bag_service"
                )
            )
        client = config.bag_service.build_client()
        data = {"huisnummer": check_house_number, "postcode": check_postal}

        try:
            cls.make_request(client, data)
        except (HTTPError, ClientError) as e:
            e = e.__cause__ or e
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=e)
            )

    @classmethod
    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:bag_bagconfig_change",
                    args=(BAGConfig.singleton_instance_id,),
                ),
            ),
        ]
