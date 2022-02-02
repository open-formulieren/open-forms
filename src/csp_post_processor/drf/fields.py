"""
Django Rest Framework integration to apply post processing for serializer fields.
"""
import logging

from rest_framework import fields

from ..processor import post_process_html

logger = logging.getLogger(__name__)


class CSPPostProcessedHTMLField(fields.CharField):
    """
    Post process a CharField containing HTML, injecting the required CSP nonce.

    Note that the underlying data is expected to be HTML and will be processed as such.

    The parent serializer must have the HTTP request in the context for this to work,
    as the CSP Nonce to use is taken from a request header.
    """

    def to_representation(self, value):
        str_value: str = super().to_representation(value)

        # the request from the context is required for post-processing, but there is no
        # guarantee this is always present!
        if not (request := self.parent.context.get("request")):
            logger.warning(
                "Cannot CSP post-process value, there is no valid request in the "
                "serializer context. Returning original version."
            )
            return str_value

        return post_process_html(str_value, request)
