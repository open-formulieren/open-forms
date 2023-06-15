from zeep.client import Client

from .models import JccConfig


def get_client() -> Client:
    config = JccConfig.get_solo()
    assert isinstance(config, JccConfig)
    assert config.service is not None
    return config.service.build_client()
