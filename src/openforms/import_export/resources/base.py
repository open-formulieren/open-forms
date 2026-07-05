from import_export.resources import ModelResource

from openforms.forms.models import Form


class BaseResource(ModelResource):
    def export_for_form(self, form: Form):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement export_for_form()"
        )
