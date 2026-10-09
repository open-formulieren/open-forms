from django.contrib import admin
from django.http import HttpRequest

from ..models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "open_product")

    def get_readonly_fields(
        self, request: HttpRequest, obj: Product | None = None
    ) -> list[str]:
        if obj and obj.producttype:
            return ["name", "uuid", "producttype", "price"]
        return []

    def open_product(self, instance: Product) -> bool:
        return bool(instance.producttype)

    open_product.boolean = True  # pyright:ignore[reportFunctionMemberAccess]
