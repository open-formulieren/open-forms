"""
Provide API client implementations for the objects API registration plugin.

The clients used are:

* Objects API client, to register the form submission
* Documenten API client, for attachments related to the created object
* Catalogi API client, for displaying contextually relevant possible document types
  in the form builder
"""

from openforms.contrib.objects_api.clients import ObjectsClient
from openforms.contrib.zgw.clients import DocumentenClient
from zgw_consumers_ext.api_client import NLXClient, build_client

from .models import ObjectsAPIConfig


class NoServiceConfigured(RuntimeError):
    pass


def get_objects_client() -> NLXClient:
    config = ObjectsAPIConfig.get_solo()
    assert isinstance(config, ObjectsAPIConfig)
    if not (service := config.objects_service):
        raise NoServiceConfigured("No Objects API service configured!")
    return build_client(service, client_factory=ObjectsClient)


def get_documents_client() -> DocumentenClient:
    config = ObjectsAPIConfig.get_solo()
    assert isinstance(config, ObjectsAPIConfig)
    if not (service := config.drc_service):
        raise NoServiceConfigured("No Documents API service configured!")
    return build_client(service, client_factory=DocumentenClient)
