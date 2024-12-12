"""
Provide API client implementations for the ZGW APIs registration plugin.

The clients used are:

* Zaken API client, to register the form submission
* Documenten API client, for attachments related to the created object
* Catalogi API client, for displaying contextually relevant possible document types
  in the form builder
"""

from zgw_consumers.client import build_client

from openforms.contrib.zgw.clients import CatalogiClient, DocumentenClient, ZakenClient

from .models import ZGWApiGroupConfig


def get_zaken_client(config: ZGWApiGroupConfig) -> ZakenClient:
    service = config.zrc_service
    assert service is not None
    return build_client(service, client_factory=ZakenClient)


def get_documents_client(config: ZGWApiGroupConfig) -> DocumentenClient:
    service = config.drc_service
    assert service is not None
    return build_client(service, client_factory=DocumentenClient)


def get_catalogi_client(config: ZGWApiGroupConfig) -> CatalogiClient:
    service = config.ztc_service
    assert service is not None
    return build_client(service, client_factory=CatalogiClient)
