from django.contrib import admin

from ..models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "open_product")

    def open_product(self, instance: Product) -> bool:
        return bool(instance.producttype)

    open_product.boolean = True  # pyright:ignore[reportFunctionMemberAccess]
