from openforms.forms.models import Category, Form

from .base import BaseResource


class CategoryResource(BaseResource):
    class Meta:
        model = Category
        fields = ("uuid", "name")

    def export_for_form(self, form: Form):
        return self.export(
            queryset=[form.category] if form.category is not None else []
        )
