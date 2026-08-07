from uuid import uuid4

from openforms.forms.models import Form
from openforms.products.models import Product

from .base import BaseResource


class ProductResource(BaseResource):
    deep_comparison_fields = ("name", "price", "information")
    identifier_field = "uuid"

    class Meta:
        model = Product
        import_id_fields = ("uuid",)
        fields = ("uuid", "name", "price", "information")
        store_instance = True
        store_row_values = True

    def export_for_form(self, form: Form):
        return self.export(queryset=[form.product] if form.product is not None else [])

    def generate_identifier(self, row):
        return uuid4()
