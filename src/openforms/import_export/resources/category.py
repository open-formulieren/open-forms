from openforms.forms.models import Category, Form

from .base import BaseResource


class CategoryResource(BaseResource):
    deep_comparison_fields = ("name", "path", "depth")

    class Meta:
        model = Category
        import_id_fields = ("uuid",)
        fields = ("uuid", "name", "path", "depth")
        store_instance = True
        store_row_values = True

    def export_for_form(self, form: Form):
        return self.export(
            queryset=[form.category] if form.category is not None else []
        )
