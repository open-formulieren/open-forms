from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from rest_framework.serializers import ModelSerializer

from .drf.fields import CSPPostProcessedHTMLField
from .fields import CSPPostProcessedWYSIWYGField


class CSPPostProcessConfig(AppConfig):
    name = "csp_post_processor"
    verbose_name = _("CSP post-processor")

    def ready(self):
        update_drf_modelserializer_mapping()


def update_drf_modelserializer_mapping() -> None:
    mapping = ModelSerializer.serializer_field_mapping
    mapping[CSPPostProcessedWYSIWYGField] = CSPPostProcessedHTMLField
