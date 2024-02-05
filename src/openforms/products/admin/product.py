from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ..models import Product


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def clean_price(self):
        value = self.cleaned_data["price"]
        if value <= 0:
            raise ValidationError(_("The value must be greater than 0."))

        return value


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
