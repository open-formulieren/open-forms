import json
import os

from django.contrib import admin  # messages
from django.shortcuts import redirect, render
from django.urls import path, reverse, reverse_lazy

from openforms.forms.models.form import Form
from openforms.forms.models.form_definition import FormDefinition
from openforms.forms.models.form_step import FormStep
from openforms.products.admin.utils import get_initial_fields_steps_tupels

from ..json_schema_importer.entry import convert_json_schema_to_py
from ..models import Product
from .form import SchemaImportForm, StepForm


class ProductJsonSchemaMixin:
    schema_steps_template = "admin/products/product/schema_steps.html"
    import_form = SchemaImportForm
    fields_tuples = [
        (),
    ]
    schema = None

    def get_steps(self, request, extra_content=None):
        if request.method == "POST":
            form = StepForm(self.fields_tuples, request.POST)
            if form.is_valid():
                # not sure if we can user for.changed() ->  data = {i: form.cleaned_data[i] for i in form.changed_data}
                sorted_data = sorted([(v, k) for k, v in form.cleaned_data.items()])
                try:
                    # logic to create objetcs: form,form_definition and form_steps object
                    if self.schema is not None:
                        formio_collection = convert_json_schema_to_py(
                            json_schema=self.schema
                        )
                        form_obj = Form.objects.create(
                            name=self.schema["title"],
                            active=True,
                            authentication_backends=["demo"],
                        )
                        """
                        if   initial step == 1 not changed => default flow with all fields in one step
                        else initial step changed in one or more inputs and formio_collection will be devided
                        """
                        # there is a BUG bellow: think of corrrect way to create an obj of FormDefinition
                        initial_step = 1
                        for elem in sorted_data:
                            # may be to check for the next elem[0] == prev
                            for elem_dict in formio_collection["components"]:
                                temp_dict = {"components": []}
                                if elem[1] in elem_dict:
                                    temp_dict["components"].append(elem_dict)
                            form_def = FormDefinition.objects.create(
                                name="Prod1", configuration=temp_dict
                            )
                            form_step = FormStep.objects.create(
                                form=form_obj, form_definition=form_def, order=elem[0]
                            )
                            print(form_step.order)  # order is right

                except Exception as e:
                    print("smth went wrong", e)
            else:
                print("errors are", form.errors)
                # BUG
                # this redirect not possible: no GET request: return redirect(reverse("admin:products_product_check_steps"))
            return redirect(reverse("admin:products_product_import"))

    def make_form_steps(self, request, extra_context=None):
        """
        return template with form and process data if form is bound->
        create form instnace of Open Forms with 1 step as default;
        or different steps if
        current state: no API to fetch JSON schema product yet; so user local file as a src of JSON schema
        """

        if request.method == "POST":
            form = SchemaImportForm(request.POST, request.FILES)
            if form.is_valid():
                module_dir = os.path.dirname(__file__)
                file_path = os.path.join(module_dir, "json_schema.json")
                with open(file_path) as fh:
                    json_data = fh.read()
                    schema = json.loads(json_data)
                self.fields_tuples = get_initial_fields_steps_tupels(schema)
                self.schema = schema
                return redirect(reverse("admin:products_product_form_step"))

        if request.method == "GET":

            form = StepForm(self.fields_tuples)

        return render(
            request,
            self.schema_steps_template,
            {"form": form},
        )

    def get_urls(self):
        urls = super().get_urls()
        add_urls = [
            path(
                "step/",
                self.admin_site.admin_view(self.make_form_steps),
                name="products_product_form_step",
            ),
            path(
                "step-choice/",
                self.admin_site.admin_view(self.get_steps),
                name="products_product_get_steps",
            ),
            path(
                "step-choice-change/",
                self.admin_site.admin_view(self.get_steps),
                name="products_product_check_steps",
            ),
        ]
        return add_urls + urls


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
class ProductAdmin(ProductImportMixin, ProductJsonSchemaMixin, admin.ModelAdmin):
    pass
