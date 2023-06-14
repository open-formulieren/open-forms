from zeep.client import Client

from .models import JccConfig


def get_client() -> Client:
    service = JccConfig.get_solo().service
    assert service is not None
    return service.build_client()
