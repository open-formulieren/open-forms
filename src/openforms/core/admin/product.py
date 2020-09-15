from django.contrib import admin

from openforms.core.models import Product


class ProductAdmin(admin.ModelAdmin):
    pass


admin.site.register(Product, ProductAdmin)
