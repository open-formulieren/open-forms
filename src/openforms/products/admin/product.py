from collections import defaultdict

from django import forms
from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from openforms.typing import StrOrPromise

from ..models import Product


class OpenProductListFilter(admin.SimpleListFilter):
    title = _("Open Product product")
    parameter_name = "open_product"

    def lookups(self, request, model_admin):
        return [
            ("true", _("True")),
            ("false", _("False")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(producttype_uuid__isnull=False)
        elif self.value() == "false":
            return queryset.filter(producttype_uuid__isnull=True)


class ProductAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields["uuid"].required = False  # see default on model
            self.fields["name"].required = False  # required for local products
            self.fields["price"].required = False  # required for local products

    def clean(self):
        super().clean()

        errors: dict[str, list[StrOrPromise]] = defaultdict(list)
        is_update = bool(self.instance.pk)
        producttype_uuid = self.cleaned_data.get("producttype_uuid")
        name = self.cleaned_data.get("name")
        # Note that the name field is readonly when a producttype_uuid is set,
        # hence no extra validation should have to be added here for the update scenario.
        if not is_update and (producttype_uuid and name):
            errors["name"].append(
                _("Name cannot be filled in for products with a producttype ID.")
            )
        elif not is_update and not any((name, producttype_uuid)):
            errors["name"].append(
                _("Name is required for products without a producttype ID.")
            )

        if errors:
            raise forms.ValidationError(errors)

    class Meta:
        fields = (
            "uuid",
            "producttype_uuid",
            "price",
            "name",
            "information",
        )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "open_product")
    list_filter = (OpenProductListFilter,)

    form = ProductAdminForm

    def get_readonly_fields(
        self, request: HttpRequest, obj: Product | None = None
    ) -> list[str]:
        if obj and obj.producttype_uuid:
            return ["name", "uuid", "producttype_uuid", "price"]
        return []

    @admin.display(description=_("from Open Product?"), boolean=True)
    def open_product(self, instance: Product) -> bool:
        return bool(instance.producttype_uuid)
