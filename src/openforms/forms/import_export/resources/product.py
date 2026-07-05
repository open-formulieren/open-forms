from openforms.forms.models import Form
from openforms.products.models import Product

from .base import BaseResource


class ProductResource(BaseResource):
    class Meta:
        model = Product
        fields = ("uuid", "name", "price", "information")

    def export_for_form(self, form: Form):
        return self.export(queryset=[form.product] if form.product is not None else [])
