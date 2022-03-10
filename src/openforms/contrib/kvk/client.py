import logging

import elasticapm
from requests import HTTPError, RequestException
from zds_client import ClientError

from openforms.contrib.kvk.models import KVKConfig

logger = logging.getLogger(__name__)


class KVKClientError(Exception):
    pass


class KVKSearchClient:
    # https://api.kvk.nl/api/v1/zoeken?x=y
    # https://api.kvk.nl/test/api/v1/zoeken?x=y
    # docs: https://developers.kvk.nl/apis/zoeken

    @elasticapm.capture_span("app.kvk")
    def query(self, **query_params):
        config = KVKConfig.get_solo()
        if not config.service:
            logger.warning("no service defined for KvK client")
            raise KVKClientError("no service defined")

        client = config.service.build_client()

        try:
            results = client.operation(
                "getResults",
                method="GET",
                data=None,
                request_kwargs=dict(
                    params=query_params,
                ),
            )
        except (RequestException, ClientError) as e:
            logger.exception("exception while making KVK request", exc_info=e)
            raise e
        else:
            return results


class KVKProfileClient:
    # https://api.kvk.nl/api/v1/basisprofielen/{kvkNummer}/hoofdvestiging
    # https://api.kvk.nl/test/api/v1/basisprofielen/{kvkNummer}/hoofdvestiging
    # docs: https://developers.kvk.nl/apis/basisprofiel

    @elasticapm.capture_span("app.kvk")
    def query(self, kvkNummer):
        config = KVKConfig.get_solo()
        if not config.profiles:
            logger.warning("no service defined for KvK client")
            raise KVKClientError("no service defined")

        client = config.profiles.build_client()

        try:
            results = client.operation(
                "getBasisprofielByKvkNummer",
                method="GET",
                data=None,
                kvkNummer=kvkNummer,
            )
        except RequestException as e:
            logger.exception("exception while making KVK request", exc_info=e)
            raise e
        except ClientError as e:
            if (
                not isinstance(e.__cause__, HTTPError)
                or e.__cause__.response.status_code != 404
            ):
                logger.exception("exception while making KVK request", exc_info=e)
            raise e
        else:
            return results
