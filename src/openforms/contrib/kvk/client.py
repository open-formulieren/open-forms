import logging

from requests import RequestException
from zds_client import ClientError

from openforms.contrib.kvk.models import KVKConfig

logger = logging.getLogger(__name__)


class KVKClientError(Exception):
    pass


class KVKClient:
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
        except RequestException as e:
            logger.exception("exception while making KVK request", exc_info=e)
            raise e
        except ClientError as e:
            logger.exception("exception while making KVK request", exc_info=e)
            raise e
        else:
            return results
