from dataclasses import dataclass
from functools import wraps

from django.utils.cache import patch_vary_headers
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
