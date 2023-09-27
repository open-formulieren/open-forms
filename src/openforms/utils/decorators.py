from dataclasses import dataclass
from functools import wraps

from django.contrib import admin
from django.db import models
from django.utils.cache import patch_vary_headers
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache as django_never_cache

import requests

from openforms.config.models import GlobalConfiguration

X_ROBOTS_TAG_HEADER = "X-Robots-Tag"


def never_cache(view_func):
    """
    Decorator that wraps around Django's never_cache, adding the "Pragma" header.

    Django doesn't add the ``Pragma: no-cache`` header by itself, but it is desired
    by users of Open Forms, so we add it.
    """

    @django_never_cache
    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response["Pragma"] = "no-cache"
        return response

    return _wrapped_view_func


@dataclass
class IndexingOptions:
    block: bool
    content: str


def conditional_search_engine_index(config_attr: str, content="noindex, nofollow"):
    """
    Conditially allow search engines to list the page in their search results.

    Applying this decorator exposes ``request.indexing_options``, which is a
    :class:`IndexingOptions` instance.

    If indexing is not allowed, the X_ROBOTS_TAG_HEADER will be emitted in the response.

    :arg config_attr: Name of the configuration attribute from the
      :class:`GlobalConfiguration` class.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view_func(request, *args, **kwargs):
            config = GlobalConfiguration.get_solo()
            allow_indexing = getattr(config, config_attr)
            assert not hasattr(request, "indexing_options")
            # set custom attribute on request so that the template engine has access as well
            request.indexing_options = IndexingOptions(
                block=not allow_indexing, content=content
            )
            response = view_func(request, *args, **kwargs)
            patch_vary_headers(response, (X_ROBOTS_TAG_HEADER,))
            if not allow_indexing:
                response[X_ROBOTS_TAG_HEADER] = content
            return response

        return _wrapped_view_func

    return decorator


def suppress_requests_errors(model: type[models.Model], fields: list[str]):
    """
    Add robustness to admin fields making outgoing requests that may fail.

    If a :class:`requests.RequestException`is caught, return the base (non-enhanced)
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
