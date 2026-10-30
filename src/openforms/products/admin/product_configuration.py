from django import forms
from django.contrib import admin
from django.core.cache import cache
from django.utils.translation import gettext as _

from openproduct_client.structs.base import PaginatedResponseBody
from openproduct_client.structs.product_type import ContentLabel
from solo.admin import SingletonModelAdmin

from ..client import get_open_product_client
from ..constants import CONTENT_LABELS_LOOKUP_CACHE_TIMEOUT
from ..models import ProductConfiguration


class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        fields = (
            "open_product_service",
            "content_labels",
        )

    def clean(self):
        cleaned_data = super().clean() or {}

        form_labels = cleaned_data.get("content_labels")
        form_service = cleaned_data.get("open_product_service")

        if not form_labels or not form_service:
            return cleaned_data

        with get_open_product_client(form_service) as client:
            # django types do not help us here (ANY | None)
            result: PaginatedResponseBody[ContentLabel] | None = cache.get_or_set(
                key=f"content_labels|get_content_labels|{form_service.slug}",
                default=client.content_label.list,
                timeout=CONTENT_LABELS_LOOKUP_CACHE_TIMEOUT,
            )

            assert result is not None

            results = result.results
            fetched_labels = {item.naam for item in results}
            unknown_labels = [
                label for label in form_labels if label not in fetched_labels
            ]

            if unknown_labels:
                self.add_error(
                    "content_labels",
                    _("Unknown labels were provided: {labels}.").format(
                        labels=", ".join(sorted(unknown_labels))
                    ),
                )

        return cleaned_data


@admin.register(ProductConfiguration)
class ProductConfigurationAdmin(SingletonModelAdmin):
    form = ProductConfigurationForm
