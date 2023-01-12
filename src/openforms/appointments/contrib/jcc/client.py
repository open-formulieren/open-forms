from .models import JccConfig


def get_client():
    service = JccConfig.get_solo().service
    assert service is not None
    return service.build_client()
