from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.forms.models import Form

from .base import BaseResource


class YiviAttributeGroupResource(BaseResource):
    deep_comparison_fields = ("name", "description", "attributes")

    class Meta:
        model = AttributeGroup
        import_id_fields = ("uuid",)
        fields = ("uuid", "name", "description", "attributes")
        store_instance = True
        store_row_values = True

    def export_for_form(self, form: Form):
        yivi_auth_backend = form.auth_backends.all().filter(backend="yivi_oidc").first()
        if yivi_auth_backend is None:
            return self.export(queryset=[])

        return self.export(
            queryset=AttributeGroup.objects.filter(
                uuid__in=yivi_auth_backend.options["additional_attributes_groups"]
            )
        )
