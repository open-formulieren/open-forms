from functools import wraps

from django.utils.cache import add_never_cache_headers


def response_api_headers(view_func):
    """
    Decorator. Add certain HTTP headers to API responses based on django settings.
    Pragma and Cache-Control are added to prevent browsers from caching API responses.
    * This is done for security reasons.
    """

    @wraps(view_func)
    def _wrapped_view_func(*args, **kwargs):
        response = view_func(*args, **kwargs)
        add_never_cache_headers(response)
        response["Pragma"] = "no-cache"
        return response

    return _wrapped_view_func
