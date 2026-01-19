from django.contrib import admin

from ..models import PriceOption, Product


class PriceOptionInline(admin.TabularInline):
    model = PriceOption
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = (PriceOptionInline,)
    pass
