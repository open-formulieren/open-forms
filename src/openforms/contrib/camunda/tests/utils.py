import base64
import os
from unittest import skipIf
from urllib.parse import urlparse

from django_camunda.client import Camunda, get_client
from django_camunda.models import CamundaConfig

from openforms.tests.utils import can_connect

# support configuration through envvars for tests/CI
CAMUNDA_USER = os.getenv("CAMUNDA_USER", "demo")
CAMUNDA_PASSWORD = os.getenv("CAMUNDA_PASSWORD", "demo")
CAMUNDA_API_BASE_URL = os.getenv(
    "CAMUNDA_API_BASE_URL", "http://localhost:8080/engine-rest/"
)


def require_camunda(func):
    """
    Decorator to skip test(s) if Camunda is not available.
    """
    parsed = urlparse(CAMUNDA_API_BASE_URL)
    conn_available = can_connect(parsed.netloc)
    reason = (
        f"Cannot connect to Camunda host '{CAMUNDA_API_BASE_URL}'. You can bring "
        "the services up with docker-compose, see the 'docker/camunda' folder."
    )
    return skipIf(not conn_available, reason)(func)


def get_camunda_client() -> Camunda:
    """
    Get a camunda client object that can connect to the configured instance.
    """
    parsed = urlparse(CAMUNDA_API_BASE_URL)
    basic_auth = f"{CAMUNDA_USER}:{CAMUNDA_PASSWORD}"
    b64 = base64.b64encode(basic_auth.encode()).decode()
    config = CamundaConfig(
        root_url=f"{parsed.scheme}://{parsed.netloc}",
        rest_api_path=parsed.path[1:],  # cut off leading slash
        auth_header=f"Basic {b64}",
    )
    return get_client(config=config)
