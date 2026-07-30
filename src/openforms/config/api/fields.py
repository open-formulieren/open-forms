from rest_framework import serializers

from csp_post_processor.drf.fields import CSPPostProcessedHTMLField

from ..models import GlobalConfiguration


class GlobalConfigurationLookupMixin:
    def get_attribute(self, instance):
        # inject our global configuration instance instead
        instance = GlobalConfiguration.get_solo()
        return super().get_attribute(instance)  # pyright: ignore[reportAttributeAccessIssue]


class GlobalConfigurationCSPPostProcessedHTMLField(
    GlobalConfigurationLookupMixin, CSPPostProcessedHTMLField
):
    pass


class GlobalConfigurationImageField(
    GlobalConfigurationLookupMixin, serializers.ImageField
):
    pass
