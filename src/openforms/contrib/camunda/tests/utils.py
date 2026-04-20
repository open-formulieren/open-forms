import base64

from django_camunda.models import CamundaConfig


class CamundaMixin:
    """
    Mixin to use Camunda in unit tests
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # use docker compose fixtures
        cls.config = CamundaConfig.get_solo()
        cls.config.root_url = "http://localhost:8080/"
        cls.config.rest_api_path = "engine-rest/"
        b64 = base64.b64encode(b"demo:demo").decode()
        cls.config.auth_header = f"Basic {b64}"
        cls.config.save()

        cls.addClassCleanup(CamundaConfig.clear_cache)
