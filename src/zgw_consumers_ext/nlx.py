import json
import logging

from ape_pie import APIClient
from requests import JSONDecodeError
from requests.models import PreparedRequest, Request, Response
from requests.utils import guess_json_utf
from zgw_consumers.nlx import Rewriter

logger = logging.getLogger(__name__)


def nlx_rewrite_hook(response: Response, *args, **kwargs):
    try:
        json_data = response.json()
    # it may be a different content type than JSON! Checking for application/json
    # content type header is a bit annoying because there are alternatives like
    # application/hal+json :(
    except JSONDecodeError:
        return response

    # rewrite the JSON
    logger.debug(
        "NLX client: Rewriting response JSON to replace outway URLs",
        extra={"request": response.request},
    )
    # apply similar logic to response.json() itself
    encoding = (
        response.encoding
        or guess_json_utf(response.content)
        or response.apparent_encoding
    )
    assert encoding
    rewriter = Rewriter()
    rewriter.backwards(json_data)
    response._content = json.dumps(json_data).encode(encoding)

    return response


class NLXMixin:
    base_url: str

    def __init__(self, *args, nlx_base_url: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.nlx_base_url = nlx_base_url

        if self.nlx_base_url:
            self.hooks["response"].insert(0, nlx_rewrite_hook)  # type: ignore

    def prepare_request(self, request: Request) -> PreparedRequest:
        prepared_request = super().prepare_request(request)  # type: ignore

        if not self.nlx_base_url:
            return prepared_request

        # change the actual URL being called so that it uses NLX
        # XXX: it would be really nice if at some point NLX would be just a normal HTTP
        # proxy so we can instead just map DB configuration to proxy setup.
        new_url = (original := prepared_request.url).replace(
            self.base_url, self.nlx_base_url, 1
        )
        logger.debug(
            "NLX client: URL %s rewritten to %s",
            original,
            new_url,
            extra={
                "original_url": original,
                "base_url": self.base_url,
                "nlx_base_url": self.nlx_base_url,
                "client": self,
            },
        )
        prepared_request.url = new_url

        return prepared_request


class NLXClient(NLXMixin, APIClient):
    pass
