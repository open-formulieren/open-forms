from django.contrib import admin

from .product import ProductAdmin
from .form_definition import FormDefinitionAdmin

from openforms.core.models import FormDefinition, Product


admin.site.register(Product, ProductAdmin)
admin.site.register(FormDefinition, FormDefinitionAdmin)
