from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.forms.models import Form

from .base import BaseResource


class YiviAttributeGroupResource(BaseResource):
    class Meta:
        model = AttributeGroup
        fields = ("uuid", "name", "description", "attributes")

    def export_for_form(self, form: Form):
        yivi_auth_backend = form.auth_backends.all().filter(backend="yivi_oidc").first()
        if (
            yivi_auth_backend is None
            or "additional_attributes_groups" not in yivi_auth_backend.options
        ):
            return self.export(queryset=[])

        return self.export(
            queryset=AttributeGroup.objects.filter(
                uuid__in=yivi_auth_backend.options["additional_attributes_groups"]
            )
        )
