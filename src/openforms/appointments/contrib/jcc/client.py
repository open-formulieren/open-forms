from zeep.client import Client

from soap.client import build_client

from .models import JccConfig


def get_client() -> Client:
    config = JccConfig.get_solo()
    assert config.service is not None
    return build_client(config.service)
