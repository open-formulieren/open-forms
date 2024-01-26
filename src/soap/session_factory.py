"""
Define a session factory from SOAPService model.

The resulting session (a :class:`requests.Session` instance) can (and should) be fed
to the Zeep client transport. You can also use the session directly if you're not using
a SOAP library, but we advise against that.

.. note:: This is similar to the ServiceClientFactory for other flavours, but because
   the actual client is a :class:`zeep.Client``, other nomenclature is used to avoid
   confusion.
"""

from dataclasses import dataclass
from typing import Any

from .models import SoapService


@dataclass
class SessionFactory:
    service: SoapService

    def get_client_base_url(self) -> str:
        return self.service.url

    def get_client_session_kwargs(self) -> dict[str, Any]:
        kwargs = {
            "verify": self.service.get_verify(),
            "cert": self.service.get_cert(),
            "auth": self.service.get_auth(),
        }
        return kwargs
