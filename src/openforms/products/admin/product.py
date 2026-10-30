from collections import defaultdict

from django import forms
from django.contrib import admin
from django.db.models import Q
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from openforms.typing import StrOrPromise

from ..constants import ProductSourceChoices
from ..models import Product


class OpenProductListFilter(admin.SimpleListFilter):
    title = _("External product")
    parameter_name = "is_external_product"

    def lookups(self, request, model_admin):
        return [
            ("true", _("True")),
            ("false", _("False")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(~Q(product_source=ProductSourceChoices.local))
        elif self.value() == "false":
            return queryset.filter(product_source=ProductSourceChoices.local)


class ProductAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields["uuid"].required = False  # see default on model
            self.fields["name"].required = False  # required for local products
            self.fields["price"].required = False  # required for local products

    def clean(self):
        cleaned_data = super().clean() or {}

        errors: dict[str, list[StrOrPromise]] = defaultdict(list)
        is_update = bool(self.instance.pk)
        product_source = cleaned_data.get("product_source")
        product_type_uuid = cleaned_data.get("producttype_uuid")
        name = cleaned_data.get("name")

        if not is_update:
            is_local = product_source == ProductSourceChoices.local

            if is_local and product_type_uuid:
                errors["producttype_uuid"].append(
                    _("Product type ID cannot be defined for local products.")
                )
            if not is_local and not product_type_uuid:
                errors["producttype_uuid"].append(
                    _("Product type ID is required for external products.")
                )
            if not is_local and name:
                errors["name"].append(
                    _("Name cannot be filled in for external products.")
                )
            if is_local and not name:
                errors["name"].append(_("Name is required for local products."))

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data

    class Meta:
        fields = (
            "uuid",
            "product_source",
            "producttype_uuid",
            "price",
            "name",
            "information",
        )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_source", "external_product")
    list_filter = (OpenProductListFilter,)

    form = ProductAdminForm

    def get_readonly_fields(
        self, request: HttpRequest, obj: Product | None = None
    ) -> list[str]:
        if (
            obj
            and obj.product_source != ProductSourceChoices.local
            and obj.producttype_uuid
        ):
            return ["uuid", "product_source", "producttype_uuid", "price", "name"]
        # this prevents users from trying to modify a local to an external product which
        # causes a lot of problems now. This will be fixed with the proper UI changes.
        elif obj and obj.product_source == ProductSourceChoices.local:
            return ["product_source", "producttype_uuid"]

        return []

    @admin.display(description=_("external product"), boolean=True)
    def external_product(self, instance: Product) -> bool:
        return bool(instance.product_source != ProductSourceChoices.local)
