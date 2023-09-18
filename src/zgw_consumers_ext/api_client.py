from dataclasses import dataclass
from typing import Any

from zgw_consumers.models import Service


@dataclass
class ServiceClientFactory:
    service: Service

    def get_client_base_url(self) -> str:
        return self.service.api_root

    def get_client_session_kwargs(self) -> dict[str, Any]:
        kwargs = {}

        # mTLS: verify server certificate if configured
        if server_cert := self.service.server_certificate:
            # NOTE: this only works with a file-system based storage!
            kwargs["verify"] = server_cert.public_certificate.path

        # mTLS: offer client certificate if configured
        if client_cert := self.service.client_certificate:
            client_cert_path = client_cert.public_certificate.path
            # decide between single cert or cert,key tuple variant
            kwargs["cert"] = (
                (client_cert_path, privkey.path)
                if (privkey := client_cert.private_key)
                else client_cert_path
            )

        return kwargs
