import json
import os

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _

from openforms.forms.models.form import Form
from openforms.forms.models.form_definition import FormDefinition

from ..json_schema_importer.entry import convert_json_schema_to_py
from ..models import Product
from .form import SchemaImportForm


class ProductImportMixin:
    import_template = "admin/products/product/import_product.html"
    import_form = SchemaImportForm
    success_url = reverse_lazy("admin:products_product_changelist")

    def import_schema(self, request, extra_context=None):
        """
        return template with form and process data if form is bound->
        create form instnace of Open Forms with 1 step;
        note: for now reading JSON schema from a local file  (should be changed)

        """

        url_success = "admin:products_product_import"
        if request.method == "POST":
            form = SchemaImportForm(request.POST, request.FILES)
            if form.is_valid():
                # file = form.cleaned_data["file"]
                # json schema from local file
                # TODO (add validation for ext =='json')
                module_dir = os.path.dirname(__file__)
                file_path = os.path.join(module_dir, "json_schema.json")
                with open(file_path) as fh:
                    json_data = fh.read()
                    py_dict = json.loads(json_data)

                formio_collection = convert_json_schema_to_py(json_schema=py_dict)
                form_instance = Form.objects.create(
                    name=py_dict["title"], active=True, authentication_backends=["demo"]
                )
                form_definition = FormDefinition.objects.create(
                    name="Product velden", configuration=formio_collection
                )

                return redirect(reverse(url_success))  # can be changed

            if not form.is_valid():
                messages.add_message(request, messages.WARNING, "smth went wrong")

        form = SchemaImportForm()

        return render(
            request,
            self.import_template,
            {"form": form},
        )

    def get_urls(self):
        urls = super().get_urls()
        add_urls = [
            path(
                "import/",
                self.admin_site.admin_view(self.import_schema),
                name="products_product_import",
            ),
        ]
        return add_urls + urls


@admin.register(Product)
class ProductAdmin(ProductImportMixin, admin.ModelAdmin):
    pass
