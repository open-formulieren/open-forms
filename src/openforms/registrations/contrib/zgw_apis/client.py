"""
Provide API client implementations for the ZGW APIs registration plugin.

The clients used are:

* Zaken API client, to register the form submission
* Documenten API client, for attachments related to the created object
* Catalogi API client, for displaying contextually relevant possible document types
  in the form builder
"""

from openforms.contrib.zgw.clients import CatalogiClient, DocumentenClient, ZakenClient
from zgw_consumers_ext.api_client import build_client

from .models import ZGWApiGroupConfig


class NoServiceConfigured(RuntimeError):
    pass


def get_zaken_client(config: ZGWApiGroupConfig) -> ZakenClient:
    if not (service := config.zrc_service):
        raise NoServiceConfigured("No Zaken API service configured!")
    return build_client(service, client_factory=ZakenClient)


def get_documents_client(config: ZGWApiGroupConfig) -> DocumentenClient:
    if not (service := config.drc_service):
        raise NoServiceConfigured("No Documents API service configured!")
    return build_client(service, client_factory=DocumentenClient)


def get_catalogi_client(config: ZGWApiGroupConfig) -> CatalogiClient:
    if not (service := config.ztc_service):
        raise NoServiceConfigured("No Catalogi API service configured!")
    return build_client(service, client_factory=CatalogiClient)
