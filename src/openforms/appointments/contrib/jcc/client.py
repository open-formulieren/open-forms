from .models import JccConfig


def get_client():
    config = JccConfig.get_solo()
    return config.service.build_client()
