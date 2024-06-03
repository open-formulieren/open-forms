"""
Provide API client implementations for the objects API registration plugin.

The clients used are:

* Objects API client, to register the form submission
* Documenten API client, for attachments related to the created object
* Catalogi API client, for displaying contextually relevant possible document types
  in the form builder
"""

from zgw_consumers.client import build_client

from openforms.contrib.objects_api.clients import ObjectsClient, ObjecttypesClient
from openforms.contrib.zgw.clients import CatalogiClient, DocumentenClient

from .models import ObjectsAPIGroupConfig


class NoServiceConfigured(RuntimeError):
    pass


def get_objects_client(config: ObjectsAPIGroupConfig) -> ObjectsClient:
    if not (service := config.objects_service):
        raise NoServiceConfigured("No Objects API service configured!")
    return build_client(service, client_factory=ObjectsClient)


def get_objecttypes_client(config: ObjectsAPIGroupConfig) -> ObjecttypesClient:
    if not (service := config.objecttypes_service):
        raise NoServiceConfigured("No Objecttypes API service configured!")
    return build_client(service, client_factory=ObjecttypesClient)


def get_documents_client(config: ObjectsAPIGroupConfig) -> DocumentenClient:
    if not (service := config.drc_service):
        raise NoServiceConfigured("No Documents API service configured!")
    return build_client(service, client_factory=DocumentenClient)


def get_catalogi_client(config: ObjectsAPIGroupConfig) -> CatalogiClient:
    if not (service := config.catalogi_service):
        raise NoServiceConfigured("No Catalogi API service configured!")
    return build_client(service, client_factory=CatalogiClient)
