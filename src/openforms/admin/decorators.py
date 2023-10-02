from functools import wraps

from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

import requests


def suppress_requests_errors(model: type[models.Model], fields: list[str]):
    """
    Add robustness to admin fields which make outgoing requests that may fail.

    If a :class:`requests.RequestException` is caught, return the base (non-enhanced)
    form field that Django would generate by default and append an error message
    for the end-user.

    :arg fields: A list of model field names for which to suppress errors.
    """

    def fallback(self, db_field, request, *args, **kwargs):
        kwargs = {**self.formfield_overrides[db_field.__class__], **kwargs}

        class CustomWidget(kwargs["widget"]):
            def render(self, *args, **kwargs):
                output = super().render(*args, **kwargs)

                error_message = _(
                    "Could not load data - enable and check the request logs for more details."
                )

                html = format_html(
                    """
                    <div class="openforms-error-widget">
                        <div class="openforms-error-widget__column">
                            {}
                            <small class="openforms-error-widget openforms-error-widget--error-text">{}</small>
                        </div>
                    </div>""",
                    output,
                    error_message,
                )

                return html

        kwargs["widget"] = CustomWidget
        return db_field.formfield(**kwargs)

    def _decorator(admin_class: type[admin.ModelAdmin]):
        original_func = admin_class.formfield_for_dbfield
        for field in fields:
            assert model._meta.get_field(field)

        @wraps(original_func)
        def _wrapped(self, db_field, request, *args, **kwargs):
            field_name = db_field.name

            try:
                return original_func(self, db_field, request, *args, **kwargs)
            except requests.RequestException as exc:
                if field_name not in fields:
                    raise exc
                return fallback(self, db_field, request, *args, **kwargs)

        admin_class.formfield_for_dbfield = _wrapped

        return admin_class

    return _decorator
