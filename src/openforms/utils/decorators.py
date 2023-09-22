import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Type

from django.contrib import messages
from django.utils.cache import patch_vary_headers
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache as django_never_cache

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


def supress_requests_errors(fields: list[str] = []):
    """
    A decorator that wraps a try catch around the formfields_for_dbfields function.
    If the decorator catches an exception it will return a base formfield with
    an error message describing that an error has occurred.

    Args:
        fields (list[str], optional): _description_. Defaults to [].
    """

    def formfield_for_dbfield_wrapper(func):
        def _handle_formfield_for_dbfield_exceptions(self, db_field, request, **kwargs):
            if db_field.verbose_name not in fields:
                return func(self=self, db_field=db_field, request=request, **kwargs)

            try:
                return func(self=self, db_field=db_field, request=request, **kwargs)
            except Exception:
                kwargs = {**self.formfield_overrides[db_field.__class__], **kwargs}

                class CustomWidget(kwargs["widget"]):
                    def render(self, *args, **kwargs):
                        output = super().render(*args, **kwargs)

                        error_message = _(
                            "Could not load data - enable and check the request logs for more details"
                        )

                        html = f"""
                            <div class="openforms-error-widget">
                                <div class="openforms-error-widget__column">
                                    {output}
                                    <small class="openforms-error-widget--error-text">{error_message}</small>
                                </div>
                            </div>
                        """

                        return html

                return db_field.formfield(
                    help_text=db_field.help_text,
                    validators=db_field.validators,
                    widget=CustomWidget,
                )

        return _handle_formfield_for_dbfield_exceptions

    def model_admin_wrapper(admin_class):
        for name, func in inspect.getmembers(admin_class):
            if name == "formfield_for_dbfield":
                setattr(admin_class, name, formfield_for_dbfield_wrapper(func))

        return admin_class

    return model_admin_wrapper
